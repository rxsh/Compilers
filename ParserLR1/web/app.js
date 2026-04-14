const grammarTextView = document.getElementById("grammarTextView");
const grammarInitial = document.getElementById("grammarInitial");
const tokenInput = document.getElementById("tokenInput");
const loadedInput = document.getElementById("loadedInput");
const parseBtn = document.getElementById("parseBtn");
const maxStepsInput = document.getElementById("maxStepsInput");

let currentData = null;

parseBtn.addEventListener("click", async () => {
  if (!currentData) {
    return;
  }

  try {
    const tokens = tokenInput.value.trim() ? tokenInput.value.trim().split(/\s+/) : [];
    const response = await fetch("/api/parse", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tokens,
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
});

function renderData(data) {
  currentData = structuredClone(data);
  renderGrammar(currentData.gramatica);
  renderFirstTable(currentData.first || {});
  renderClosureTable(currentData.estados || [], currentData.transiciones || []);
  renderLRTable(currentData.tabla || []);
  renderTrace(currentData.parseo || {});
  renderTree(currentData.parseo ? currentData.parseo.arbol : null);
  tokenInput.value = (currentData.entrada || []).filter((x) => x !== "$").join(" ");
  loadedInput.textContent = (currentData.entrada || []).join(" ");
  renderConflicts(currentData.conflictos || []);
}

function renderGrammar(grammar) {
  grammarInitial.textContent = grammar.inicial_aumentado || grammar.inicial || "";

  const lines = grammar.producciones_aumentadas.map((prod, index) => `(${index}) ${prod}`);
  grammarTextView.value = lines.join("\n");
}

function renderFirstTable(first) {
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
  Object.entries(first).forEach(([key, values]) => {
    if (["x", "y", "id", "+", "*", "(", ")", "$", "ε"].includes(key)) {
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
  if (!table) return; // LR table removed from UI for presentation
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

function renderTrace(parseo) {
  const status = document.getElementById("parseStatus");
  const table = document.getElementById("traceTable");
  table.innerHTML = "";

  if (!parseo || !parseo.pasos) {
    status.textContent = "Sin datos";
    status.className = "status-chip";
    return;
  }

  status.className = `status-chip ${parseo.aceptada ? "ok" : "err"}`;
  status.textContent = parseo.aceptada
    ? "Cadena aceptada"
    : `Cadena rechazada: ${parseo.error || "error desconocido"}`;

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
    const stack = [...paso.pila_estados];
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
      <td>${paso.entrada.join(" ")}</td>
      <td class="accent-cell">${paso.accion}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

function renderTree(node) {
  const root = document.getElementById("treeRoot");
  root.innerHTML = "";

  if (!node) {
    root.textContent = "Todavía no hay árbol para mostrar.";
    return;
  }

  root.appendChild(buildTreeNode(node));
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
