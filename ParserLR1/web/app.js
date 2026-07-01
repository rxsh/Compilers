const grammarTextView = document.getElementById("grammarTextView");
const grammarInitial = document.getElementById("grammarInitial");
const applyGrammarBtn = document.getElementById("applyGrammarBtn");
const productionNumbers = document.getElementById("productionNumbers");
const productionTextView = document.getElementById("productionTextView");
const sourceInput = document.getElementById("sourceInput");
const loadedInput = document.getElementById("loadedInput");
const parseBtn = document.getElementById("parseBtn");
const maxStepsInput = document.getElementById("maxStepsInput");
const treeRoot = document.getElementById("treeRoot");
const treeLeftBtn = document.getElementById("treeLeftBtn");
const treeRightBtn = document.getElementById("treeRightBtn");
const exportPdfBtn = document.getElementById("exportPdfBtn");
const translationFrame = document.getElementById("translationFrame");

let currentData = null;
let isDraggingTree = false;
let dragStartX = 0;
let dragScrollLeft = 0;

parseBtn.addEventListener("click", async () => {
  runParse();
});

applyGrammarBtn.addEventListener("click", async () => {
  runParse();
});

treeLeftBtn.addEventListener("click", () => {
  treeRoot.scrollBy({ left: -220, behavior: "smooth" });
});

treeRightBtn.addEventListener("click", () => {
  treeRoot.scrollBy({ left: 220, behavior: "smooth" });
});

exportPdfBtn.addEventListener("click", () => {
  if (!currentData?.traduccion?.html_documento) {
    alert("Todavía no hay un documento traducido para exportar.");
    return;
  }

  const printWindow = window.open("", "_blank", "width=1024,height=768");
  if (!printWindow) {
    alert("No se pudo abrir la ventana de impresión.");
    return;
  }

  printWindow.document.open();
  printWindow.document.write(currentData.traduccion.html_documento);
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => {
    printWindow.print();
  }, 250);
});

treeRoot.addEventListener("mousedown", (event) => {
  isDraggingTree = true;
  treeRoot.classList.add("dragging");
  dragStartX = event.pageX - treeRoot.offsetLeft;
  dragScrollLeft = treeRoot.scrollLeft;
});

window.addEventListener("mouseup", () => {
  isDraggingTree = false;
  treeRoot.classList.remove("dragging");
});

treeRoot.addEventListener("mouseleave", () => {
  isDraggingTree = false;
  treeRoot.classList.remove("dragging");
});

treeRoot.addEventListener("mousemove", (event) => {
  if (!isDraggingTree) {
    return;
  }
  event.preventDefault();
  const x = event.pageX - treeRoot.offsetLeft;
  const walk = (x - dragStartX) * 1.3;
  treeRoot.scrollLeft = dragScrollLeft - walk;
});

treeRoot.addEventListener("wheel", (event) => {
  if (event.deltaY === 0 && event.deltaX === 0) {
    return;
  }
  event.preventDefault();
  const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
  treeRoot.scrollLeft += delta;
}, { passive: false });

treeRoot.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    treeRoot.scrollBy({ left: -160, behavior: "smooth" });
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    treeRoot.scrollBy({ left: 160, behavior: "smooth" });
  }
});

async function runParse() {
  if (!currentData) {
    return;
  }

  try {
    const response = await fetch("/api/parse", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source_text: sourceInput.value,
        grammar_text: grammarTextView.value,
        max_steps: Number(maxStepsInput.value) || 100,
      }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "No se pudo ejecutar el parseo");
    }

    renderData(data);
  } catch (error) {
    alert(error.message);
  }
}

function renderData(data) {
  currentData = structuredClone(data);
  renderGrammar(currentData.gramatica);
  renderFirstTable(currentData.first || {}, currentData.gramatica || {});
  renderClosureTable(currentData.estados || [], currentData.transiciones || []);
  renderLRTable(currentData.tabla || []);
  renderScanner(currentData.scanner || {});
  renderTrace(currentData.parseo || {});
  renderTree(currentData.parseo ? currentData.parseo.arbol : null);
  renderTranslation(currentData.traduccion || {});
  renderAllErrors(currentData);
  sourceInput.value = currentData.scanner?.fuente || "";
  loadedInput.textContent = (currentData.entrada_lexica || []).join(" ");
  renderConflicts(currentData.conflictos || []);
}

function renderGrammar(grammar) {
  grammarInitial.textContent = grammar.inicial_aumentado || grammar.inicial || "";
  grammarTextView.value = grammar.texto_fuente || "";

  const productions = grammar.producciones_aumentadas || [];
  productionNumbers.innerHTML = productions.map((_, index) => `<div>(${index})</div>`).join("");
  productionTextView.value = productions.join("\n");
}

function renderFirstTable(first, grammar) {
  const table = document.getElementById("firstTable");
  table.innerHTML = `
    <thead>
      <tr>
        <th>Nonterminal</th>
        <th>FIRST</th>
      </tr>
    </thead>
  `;

  const tbody = document.createElement("tbody");
  const hiddenSymbols = new Set([...(grammar.terminales || []), "$", "ε"]);
  Object.entries(first).forEach(([key, values]) => {
    if (hiddenSymbols.has(key)) {
      return;
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${key}</td>
      <td class="ok-cell">{${values.join(", ")}}</td>
    `;
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
}

function renderClosureTable(states, transitions) {
  const table = document.getElementById("closureTable");
  table.innerHTML = "";

  const transitionsByState = new Map();
  transitions.forEach((transition) => {
    if (!transitionsByState.has(transition.hacia)) {
      transitionsByState.set(transition.hacia, []);
    }
    transitionsByState.get(transition.hacia).push(`goto(${transition.desde}, ${transition.simbolo})`);
  });

  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr>
      <th>Goto</th>
      <th>Kernel</th>
      <th>State</th>
      <th>Closure</th>
    </tr>
  `;
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  states.forEach((state, index) => {
    const closure = state.items || [];
    const kernel = state.kernel || ["-"];
    const gotos = transitionsByState.get(index) || (index === 0 ? ["start"] : []);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${gotos.join("<br>")}</td>
      <td class="accent-cell">${kernel.join("<br>")}</td>
      <td>${state.indice}</td>
      <td class="ok-cell">${closure.join("<br>")}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

function renderLRTable(rows) {
  const table = document.getElementById("lrTable");
  if (!table) return;
  table.innerHTML = "";

  if (!rows.length) {
    return;
  }

  const actionKeys = new Set();
  const gotoKeys = new Set();

  rows.forEach((row) => {
    Object.keys(row.action || {}).forEach((key) => actionKeys.add(key));
    Object.keys(row.goto || {}).forEach((key) => gotoKeys.add(key));
  });

  const orderedActionKeys = Array.from(actionKeys);
  const orderedGotoKeys = Array.from(gotoKeys);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headRow.innerHTML = `
    <th rowspan="2">State</th>
    <th colspan="${orderedActionKeys.length || 1}">ACTION</th>
    <th colspan="${orderedGotoKeys.length || 1}">GOTO</th>
  `;

  const headRow2 = document.createElement("tr");
  headRow2.innerHTML = `
    ${orderedActionKeys.map((key) => `<th>${key}</th>`).join("")}
    ${orderedGotoKeys.map((key) => `<th>${key}</th>`).join("")}
  `;

  thead.appendChild(headRow);
  thead.appendChild(headRow2);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.estado}</td>
      ${orderedActionKeys.map((key) => `<td class="accent-cell">${row.action?.[key] ?? ""}</td>`).join("")}
      ${orderedGotoKeys.map((key) => `<td class="ok-cell">${row.goto?.[key] ?? ""}</td>`).join("")}
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

function renderScanner(scanner) {
  const table = document.getElementById("scannerTable");
  const errorBox = document.getElementById("scannerErrors");
  const debugBox = document.getElementById("scannerDebug");
  table.innerHTML = "";

  if (!scanner || !scanner.tokens) {
    errorBox.classList.add("hidden");
    debugBox.textContent = "";
    return;
  }

  const errors = scanner.errores || [];
  if (errors.length) {
    errorBox.classList.remove("hidden");
    errorBox.innerHTML = errors
      .map((error) => `L${error.linea}:C${error.columna} - ${error.mensaje}`)
      .join("<br>");
  } else {
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
  }

  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr>
      <th>Type</th>
      <th>Lexeme</th>
      <th>Line</th>
      <th>Column</th>
    </tr>
  `;
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  scanner.tokens.forEach((token) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${token.tipo}</td>
      <td>${escapeHtml(token.lexema)}</td>
      <td>${token.linea}</td>
      <td>${token.columna}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  const traceLines = ["INFO SCAN - Start scanning..."];
  (scanner.traza || []).forEach((item) => {
    const prefix = item.evento === "error" ? "ERROR SCAN" : "DEBUG SCAN";
    traceLines.push(
      `${prefix} - ${item.detalle} found at (${item.linea}:${item.columna})`
    );
  });
  traceLines.push(`INFO SCAN - Completed with ${errors.length} errors`);
  debugBox.textContent = traceLines.join("\n");
}

function renderAllErrors(data) {
  const box = document.getElementById("allErrorsBox");
  const scannerErrors = data?.scanner?.errores || [];
  const parserErrors = data?.parseo?.errores || [];

  const sections = [];
  if (scannerErrors.length) {
    sections.push(
      `<strong>Scanner (${scannerErrors.length})</strong><br>` +
        scannerErrors
          .map((error) => `L${error.linea}:C${error.columna} - ${escapeHtml(error.mensaje)}`)
          .join("<br>")
    );
  }

  if (parserErrors.length) {
    sections.push(
      `<strong>Parser (${parserErrors.length})</strong><br>` +
        parserErrors
          .map((error) => {
            const lugar = error.indice_entrada !== undefined ? `pos ${error.indice_entrada}` : `estado ${error.estado ?? "?"}`;
            return `${lugar} - ${escapeHtml(error.mensaje || "Error sintáctico")}`;
          })
          .join("<br>")
    );
  }

  if (!sections.length) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }

  box.classList.remove("hidden");
  box.innerHTML = sections.join("<hr>");
}

function renderTrace(parseo) {
  const status = document.getElementById("parseStatus");
  const table = document.getElementById("traceTable");
  table.innerHTML = "";

  if (!parseo || !parseo.pasos) {
    status.textContent = "Sin datos";
    status.className = "status-chip";
    return;
  }

  const errorCount = (parseo.errores || []).length;
  status.className = `status-chip ${parseo.aceptada ? "ok" : "err"}`;
  status.textContent = parseo.aceptada
    ? `Cadena aceptada${errorCount ? ` con ${errorCount} error(es)` : ""}`
    : `Cadena rechazada: ${parseo.error || "error desconocido"}${errorCount ? ` (${errorCount} error(es))` : ""}`;

  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr>
      <th>Step</th>
      <th>Stack</th>
      <th>Input</th>
      <th>Action</th>
    </tr>
  `;
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  parseo.pasos.forEach((paso, index) => {
    // Algunas entradas en 'pasos' son mensajes de info (ej. recuperación)
    if (paso && paso.info) {
      const lastRowBeforeInfo = tbody.lastElementChild;
      const trInfo = document.createElement("tr");
      trInfo.innerHTML = `
        <td>${index + 1}</td>
        <td colspan="3" class="alert">${escapeHtml(paso.mensaje || paso.info)}</td>
      `;
      tbody.appendChild(trInfo);

      // Si había una fila inmediatamente anterior, márcala como parte del panic-mode
      if (lastRowBeforeInfo && lastRowBeforeInfo.tagName === "TR") {
        lastRowBeforeInfo.classList.add("panic-row");
      }
      return;
    }

    const stack = Array.isArray(paso.pila_estados) ? [...paso.pila_estados] : [];
    const symbols = paso.pila_simbolos || [];
    const intercalado = [];

    for (let i = 0; i < stack.length; i++) {
      intercalado.push(stack[i]);
      if (symbols[i]) {
        intercalado.push(symbols[i]);
      }
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${intercalado.join(" ")}</td>
      <td>${(paso.entrada || []).join(" ")}</td>
      <td class="accent-cell">${paso.accion || ""}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

function renderTree(node) {
  treeRoot.innerHTML = "";
  treeRoot.scrollLeft = 0;

  if (!node) {
    treeRoot.textContent = "Todavía no hay árbol para mostrar.";
    return;
  }

  treeRoot.appendChild(buildTreeNode(node));
}

function renderTranslation(traduccion) {
  if (!traduccion || !traduccion.html_documento) {
    translationFrame.srcdoc = "<p style='font-family: sans-serif; padding: 16px'>No hay traducción disponible.</p>";
    return;
  }

  translationFrame.srcdoc = traduccion.html_documento;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function buildTreeNode(node) {
  const wrapper = document.createElement("div");
  wrapper.className = "tree";

  const current = document.createElement("div");
  current.className = "tree-node";

  const label = document.createElement("div");
  label.className = "tree-node-label";
  label.textContent = node.simbolo;
  current.appendChild(label);

  if (node.hijos && node.hijos.length) {
    const children = document.createElement("div");
    children.className = "tree-children";
    node.hijos.forEach((child) => {
      children.appendChild(buildTreeNode(child));
    });
    current.appendChild(children);
  }

  wrapper.appendChild(current);
  return wrapper;
}

function renderConflicts(conflicts) {
  const box = document.getElementById("conflictsBox");
  if (!conflicts.length) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }

  box.classList.remove("hidden");
  box.innerHTML = conflicts
    .map((conflict) =>
      `Conflicto en estado ${conflict.estado} con símbolo ${conflict.simbolo}: ${conflict.existente} / ${conflict.nuevo}`
    )
    .join("<br>");
}

async function loadInitialData() {
  try {
    const response = await fetch("/api/demo");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "No se pudieron cargar los datos iniciales");
    }

    renderData(data);
  } catch (error) {
    alert(error.message);
  }
}

loadInitialData();
