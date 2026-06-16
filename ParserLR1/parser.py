import json
import re
from dataclasses import dataclass
from scanner import EOF as SCANNER_EOF, escanear_fuente

EPSILON = "\u03b5"
EOF = "$"
DOT = "\u00b7"


def tokenizar_lista(texto):

    tokens = []
    for t in texto.split():
        if t == "()":
            tokens.append("(")
            tokens.append(")")
        else:
            tokens.append(t)

    return tokens


def leer_gramatica(ruta):

    with open(ruta, "r", encoding="UTF-8") as f:
        return leer_gramatica_desde_texto(f.read())


def leer_gramatica_desde_texto(texto):

    producciones = []
    terminales = []
    no_terminales = []
    inicial = None
    en_producciones = False
    usa_secciones = False

    for numero_linea, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue

        if linea.startswith("TERMINALES:"):
            usa_secciones = True
            datos = linea.split(":", 1)[1].strip()
            terminales = tokenizar_lista(datos)
            en_producciones = False
            continue

        if linea.startswith("NO_TERMINALES:"):
            usa_secciones = True
            datos = linea.split(":", 1)[1].strip()
            no_terminales = tokenizar_lista(datos)
            en_producciones = False
            continue

        if linea.startswith("INICIAL:"):
            usa_secciones = True
            inicial = linea.split(":", 1)[1].strip()
            en_producciones = False
            continue

        if linea.startswith("PRODUCCIONES:"):
            usa_secciones = True
            en_producciones = True
            continue

        if en_producciones or not usa_secciones:
            producciones.extend(parsear_linea_produccion(linea, numero_linea))
            continue

        raise ValueError(f"Linea fuera de seccion en linea {numero_linea}: {linea}")

    if not usa_secciones:
        no_terminales = inferir_no_terminales(producciones)
        inicial, producciones = quitar_produccion_aumentada_si_existe(
            producciones, no_terminales
        )
        terminales = inferir_terminales(producciones, no_terminales)
    elif not no_terminales:
        no_terminales = inferir_no_terminales(producciones)

    if not usa_secciones and not inicial and producciones:
        inicial = producciones[0][0]

    if usa_secciones and not terminales:
        terminales = inferir_terminales(producciones, no_terminales)

    if not no_terminales:
        raise ValueError("La gramatica debe tener al menos un no terminal")
    if not inicial:
        raise ValueError(
            "La gramatica debe declarar INICIAL o tener una produccion inicial"
        )
    if inicial not in no_terminales:
        raise ValueError("El simbolo INICIAL debe estar en NO_TERMINALES")
    if not producciones:
        raise ValueError("La gramatica debe tener al menos una produccion")

    simbolos_validos = set(terminales) | set(no_terminales)
    for lado_izq, lado_der in producciones:
        if lado_izq not in no_terminales:
            raise ValueError(f"El lado izquierdo '{lado_izq}' no esta en NO_TERMINALES")
        for simbolo in lado_der:
            if simbolo not in simbolos_validos:
                raise ValueError(
                    f"El simbolo '{simbolo}' no esta declarado como terminal o no terminal"
                )

    return terminales, no_terminales, inicial, producciones


def parsear_linea_produccion(linea, numero_linea):

    if "->" not in linea:
        raise ValueError(f"Produccion invalida en linea {numero_linea}: falta '->'")

    lado_izq, lado_der = linea.split("->", 1)
    lado_izq = lado_izq.strip()
    if not lado_izq:
        raise ValueError(
            f"Produccion invalida en linea {numero_linea}: falta lado izquierdo"
        )

    producciones = []
    alternativas = lado_der.split("|")
    for alt in alternativas:
        simbolos_der = alt.strip().split()
        if simbolos_der == [EPSILON]:
            simbolos_der = []
        producciones.append((lado_izq, simbolos_der))

    return producciones


def inferir_no_terminales(producciones):

    no_terminales = []
    for lado_izq, _ in producciones:
        if lado_izq not in no_terminales:
            no_terminales.append(lado_izq)
    return no_terminales


def inferir_terminales(producciones, no_terminales):

    terminales = []
    no_terminales_set = set(no_terminales)

    for _, lado_der in producciones:
        for simbolo in lado_der:
            if simbolo not in no_terminales_set and simbolo not in terminales:
                terminales.append(simbolo)

    return terminales


def quitar_produccion_aumentada_si_existe(producciones, no_terminales):

    if not producciones:
        return None, producciones

    lado_izq, lado_der = producciones[0]
    if lado_izq.endswith("'") and len(lado_der) == 1 and lado_der[0] in no_terminales:
        inicial = lado_der[0]
        no_terminales.remove(lado_izq)
        return inicial, producciones[1:]

    return producciones[0][0], producciones


def calcular_first(terminales, no_terminales, producciones):

    first = {}

    for t in terminales + [EOF]:
        first[t] = {t}

    first[EPSILON] = {EPSILON}

    for nt in no_terminales:
        first[nt] = set()

    cambio = True
    while cambio:
        cambio = False

        for A, B in producciones:
            rhs = set()
            i = 0

            if not B:
                rhs.add(EPSILON)

            while i < len(B):
                simbolo = B[i]
                rhs.update(first[simbolo] - {EPSILON})

                if EPSILON in first[simbolo]:
                    i += 1
                else:
                    break

            if B and i == len(B):
                rhs.add(EPSILON)

            antes = len(first[A])
            first[A].update(rhs)
            if len(first[A]) > antes:
                cambio = True

    return first


def calcular_follow(no_terminales, producciones, inicial, first):

    follow = {}

    for A in no_terminales:
        follow[A] = set()

    follow[inicial].add(EOF)

    cambio = True
    while cambio:
        cambio = False

        for A, B in producciones:
            trailer = follow[A].copy()

            for i in range(len(B) - 1, -1, -1):
                simbolo = B[i]

                if simbolo in no_terminales:
                    antes = len(follow[simbolo])
                    follow[simbolo].update(trailer)
                    if len(follow[simbolo]) > antes:
                        cambio = True

                    if EPSILON in first[simbolo]:
                        trailer = trailer.union(first[simbolo] - {EPSILON})
                    else:
                        trailer = first[simbolo].copy()
                else:
                    trailer = first[simbolo].copy()

    return follow


def calcular_first_cadena(cadena, first):

    if not cadena:
        return {EPSILON}

    resultado = set()
    i = 0

    while i < len(cadena):
        simbolo = cadena[i]
        resultado.update(first[simbolo] - {EPSILON})

        if EPSILON in first[simbolo]:
            i += 1
        else:
            break

    if i == len(cadena):
        resultado.add(EPSILON)

    return resultado


def aumentar_gramatica(inicial, no_terminales, producciones):

    nuevo_inicial = inicial + "'"
    while nuevo_inicial in no_terminales:
        nuevo_inicial += "'"

    nuevas_producciones = [(nuevo_inicial, [inicial])] + list(producciones)
    nuevos_no_terminales = [nuevo_inicial] + list(no_terminales)

    return nuevo_inicial, nuevos_no_terminales, nuevas_producciones


def agrupar_producciones(producciones):

    agrupadas = {}

    for lado_izq, lado_der in producciones:
        if lado_izq not in agrupadas:
            agrupadas[lado_izq] = []
        agrupadas[lado_izq].append(lado_der)

    return agrupadas


def formatear_produccion(lado_izq, lado_der):

    if not lado_der:
        return f"{lado_izq} -> {EPSILON}"
    return f"{lado_izq} -> {' '.join(lado_der)}"


def formatear_lookaheads(lookaheads):

    return "{" + "/".join(lookaheads) + "}"


@dataclass(frozen=True)
class ItemLR1:
    lado_izq: str
    lado_der: tuple
    punto: int
    anticipacion: str

    def simbolo_despues_punto(self):
        if self.punto < len(self.lado_der):
            return self.lado_der[self.punto]
        return None

    def avanzar_punto(self):
        return ItemLR1(self.lado_izq, self.lado_der, self.punto + 1, self.anticipacion)

    def completado(self):
        return self.punto >= len(self.lado_der)

    def texto(self):
        partes = list(self.lado_der)
        partes.insert(self.punto, DOT)
        if not self.lado_der:
            partes = [DOT]
        return f"{self.lado_izq} -> {' '.join(partes)}, {self.anticipacion}"

    def nucleo(self):
        return (self.lado_izq, self.lado_der, self.punto)

    def texto_sin_lookahead(self):
        partes = list(self.lado_der)
        partes.insert(self.punto, DOT)
        if not self.lado_der:
            partes = [DOT]
        return f"{self.lado_izq} -> {' '.join(partes)}"

    def __str__(self):
        return self.texto()


@dataclass
class NodoParseo:
    simbolo: str
    hijos: list

    def a_dict(self):
        return {
            "simbolo": self.simbolo,
            "hijos": [hijo.a_dict() for hijo in self.hijos],
        }


def escape_html(texto):

    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def crear_valor(texto="", html=None, tipo="value", extra=None):

    valor = {
        "tipo": tipo,
        "texto": str(texto),
        "html": html if html is not None else escape_html(texto),
    }
    if extra:
        valor.update(extra)
    return valor


def crear_token_semantico(token):

    if isinstance(token, dict):
        return {
            "tipo": token.get("tipo", ""),
            "lexema": token.get("lexema", token.get("tipo", "")),
            "linea": token.get("linea"),
            "columna": token.get("columna"),
        }

    return {
        "tipo": str(token),
        "lexema": str(token),
        "linea": None,
        "columna": None,
    }


def desescapar_literal_string(lexema):

    if len(lexema) >= 2 and lexema[0] == '"' and lexema[-1] == '"':
        contenido = lexema[1:-1]
    else:
        contenido = lexema

    escapes = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        '"': '"',
        "\\": "\\",
    }

    resultado = []
    i = 0
    while i < len(contenido):
        ch = contenido[i]
        if ch == "\\" and i + 1 < len(contenido):
            siguiente = contenido[i + 1]
            resultado.append(escapes.get(siguiente, siguiente))
            i += 2
            continue
        resultado.append(ch)
        i += 1

    return "".join(resultado)


def sanitizar_color_css(texto):

    texto = str(texto).strip()
    mapa_colores = {
        "rojo": "red",
        "verde": "green",
        "azul": "blue",
        "amarillo": "gold",
        "negro": "black",
        "blanco": "white",
        "gris": "gray",
        "gris oscuro": "dimgray",
        "gris claro": "lightgray",
        "morado": "purple",
        "violeta": "violet",
        "naranja": "orange",
        "rosado": "hotpink",
        "cafe": "saddlebrown",
        "marron": "brown",
        "celeste": "skyblue",
        "turquesa": "turquoise",
    }
    clave = texto.lower()
    if clave in mapa_colores:
        return mapa_colores[clave]
    if re.fullmatch(r"[a-zA-Z0-9#(),.%\s-]{1,40}", texto):
        return texto
    return "inherit"


def aplicar_funcion_documento(nombre, argumento):

    texto = argumento.get("texto", "")
    html = argumento.get("html", escape_html(texto))

    if nombre == "bold":
        return crear_valor(texto, f"<strong>{html}</strong>")
    if nombre == "italic":
        return crear_valor(texto, f"<em>{html}</em>")
    if nombre == "upper":
        return crear_valor(texto.upper(), f"<span class='fn-upper'>{escape_html(texto.upper())}</span>")
    if nombre == "lower":
        return crear_valor(texto.lower(), f"<span class='fn-lower'>{escape_html(texto.lower())}</span>")
    return crear_valor(texto, html)


def aplicar_color_documento(color_valor, contenido_valor):

    color_css = sanitizar_color_css(color_valor.get("texto", ""))
    texto = contenido_valor.get("texto", "")
    html = contenido_valor.get("html", escape_html(texto))
    return crear_valor(texto, f"<span style='color: {color_css}'>{html}</span>")


def crear_contexto_traduccion():

    return {
        "variables": {},
        "advertencias": [],
    }


def clonar_valor_semantico(valor):

    if isinstance(valor, dict):
        copia = dict(valor)
        if "items" in copia and isinstance(copia["items"], list):
            copia["items"] = list(copia["items"])
        return copia
    return valor


def resolver_identificador(nombre, contexto):

    if nombre in contexto["variables"]:
        return clonar_valor_semantico(contexto["variables"][nombre])

    contexto["advertencias"].append(
        f"Identificador '{nombre}' usado sin asignacion previa."
    )
    return crear_valor(
        nombre,
        f"<span class='identifier unresolved'>{escape_html(nombre)}</span>",
        extra={"nombre": nombre, "resuelto": False},
    )


def construir_documento_traducido(programa, contexto):

    secciones = []
    for sentencia in programa.get("items", []):
        html = sentencia.get("html", "")
        if html:
            secciones.append(html)

    if not secciones:
        secciones.append("<p class='empty-doc'>No hay salida traducida.</p>")

    cuerpo = "".join(secciones)
    html_fragmento = (
        "<main class='doc-shell'>"
        "<section class='doc-output'>"
        f"{cuerpo}"
        "</section>"
        "</main>"
    )

    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documento traducido</title>
  <style>
    body {{
      margin: 0;
      padding: 32px;
      font-family: Georgia, "Times New Roman", serif;
      background: #ffffff;
      color: #111111;
    }}
    .doc-shell {{
      max-width: 860px;
      margin: 0 auto;
    }}
    .doc-output {{
      padding: 0;
    }}
    .doc-section {{
      margin: 0 0 20px;
      font-size: 2rem;
      line-height: 1.2;
      color: #111111;
    }}
    .doc-paragraph {{
      margin: 0 0 18px;
      line-height: 1.7;
      font-size: 1.05rem;
    }}
    .doc-list {{
      margin: 0 0 18px;
      padding-left: 28px;
      line-height: 1.7;
      font-size: 1.05rem;
    }}
    .doc-list li {{
      margin-bottom: 10px;
    }}
    .identifier.unresolved {{
      color: #a63d40;
      border-bottom: 1px dashed #a63d40;
    }}
    .empty-doc {{
      margin: 0;
      color: #52606d;
      font-style: italic;
    }}
  </style>
</head>
<body>{html_fragmento}</body>
</html>"""

    return {
        "html_fragmento": html_fragmento,
        "html_documento": html_completo,
        "variables": {
            nombre: valor.get("texto", "")
            for nombre, valor in contexto["variables"].items()
        },
        "advertencias": list(contexto["advertencias"]),
    }


def aplicar_accion_semantica(indice_produccion, lado_izq, lado_der, hijos, contexto):

    if indice_produccion == 0:
        return hijos[0]
    if lado_izq == "Program":
        return {"tipo": "program", "items": hijos[0].get("items", [])}
    if lado_izq == "StmtList" and lado_der == ["Stmt", ";", "StmtList"]:
        return {"tipo": "stmtlist", "items": [hijos[0]] + hijos[2].get("items", [])}
    if lado_izq == "StmtList" and lado_der == ["Stmt"]:
        return {"tipo": "stmtlist", "items": [hijos[0]]}
    if lado_izq == "Stmt" and lado_der == ["ID", "=", "Expr"]:
        nombre = hijos[0].get("lexema", hijos[0].get("texto", "ID"))
        valor = clonar_valor_semantico(hijos[2])
        contexto["variables"][nombre] = valor
        return {
            "tipo": "stmt",
            "html": "",
            "texto": valor.get("texto", ""),
            "nombre": nombre,
            "valor": valor,
        }
    if lado_izq == "Stmt" and lado_der == ["DocStmt"]:
        return hijos[0]
    if lado_izq == "DocStmt" and lado_der == ["section", "(", "Expr", ")"]:
        valor = hijos[2]
        return {
            "tipo": "stmt",
            "html": f"<h1 class='doc-section'>{valor.get('html', '')}</h1>",
            "texto": valor.get("texto", ""),
            "valor": valor,
        }
    if lado_izq == "DocStmt" and lado_der == ["paragraph", "(", "Expr", ")"]:
        valor = hijos[2]
        return {
            "tipo": "stmt",
            "html": f"<p class='doc-paragraph'>{valor.get('html', '')}</p>",
            "texto": valor.get("texto", ""),
            "valor": valor,
        }
    if lado_izq == "DocStmt" and lado_der == ["itemize", "(", "ItemList", ")"]:
        return {
            "tipo": "stmt",
            "html": f"<ul class='doc-list'>{hijos[2].get('html', '')}</ul>",
            "texto": hijos[2].get("texto", ""),
            "valor": hijos[2],
        }
    if lado_izq == "Expr":
        partes = [hijos[0]] + hijos[1].get("items", [])
        texto = "".join(parte.get("texto", "") for parte in partes)
        html = "".join(parte.get("html", "") for parte in partes)
        return crear_valor(texto, html)
    if lado_izq == "ExprTail" and lado_der == ["+", "Term", "ExprTail"]:
        return {"tipo": "tail", "items": [hijos[1]] + hijos[2].get("items", [])}
    if lado_izq == "ExprTail" and not lado_der:
        return {"tipo": "tail", "items": []}
    if lado_izq == "Term":
        return hijos[0]
    if lado_izq == "Factor" and lado_der == ["FuncCall"]:
        return hijos[0]
    if lado_izq == "Factor" and lado_der == ["Literal"]:
        return hijos[0]
    if lado_izq == "Factor" and lado_der == ["ID"]:
        nombre = hijos[0].get("lexema", hijos[0].get("texto", ""))
        return resolver_identificador(nombre, contexto)
    if lado_izq == "Factor" and lado_der == ["(", "Expr", ")"]:
        return hijos[1]
    if lado_izq == "FuncCall" and lado_der == ["FunctionName", "(", "Expr", ")"]:
        nombre_funcion = hijos[0].get("nombre", "")
        return aplicar_funcion_documento(nombre_funcion, hijos[2])
    if lado_izq == "FuncCall" and lado_der == ["color", "(", "Expr", ",", "Expr", ")"]:
        return aplicar_color_documento(hijos[2], hijos[4])
    if lado_izq == "FunctionName":
        nombre = hijos[0].get("lexema", hijos[0].get("texto", ""))
        return {"tipo": "function", "nombre": nombre}
    if lado_izq == "Literal" and lado_der == ["STRING"]:
        texto = desescapar_literal_string(hijos[0].get("lexema", ""))
        return crear_valor(texto, escape_html(texto))
    if lado_izq == "Literal" and lado_der == ["NUMBER"]:
        texto = hijos[0].get("lexema", hijos[0].get("texto", ""))
        return crear_valor(texto, escape_html(texto))
    if lado_izq == "ItemList" and lado_der == ["item", "(", "Expr", ")", "ItemTail"]:
        valor = hijos[2]
        resto = hijos[4].get("items", [])
        items = [valor] + resto
        html = "".join(f"<li>{item.get('html', '')}</li>" for item in items)
        texto = "\n".join(item.get("texto", "") for item in items)
        return {"tipo": "items", "items": items, "html": html, "texto": texto}
    if lado_izq == "ItemTail" and lado_der == [",", "item", "(", "Expr", ")", "ItemTail"]:
        return {"tipo": "itemtail", "items": [hijos[3]] + hijos[5].get("items", [])}
    if lado_izq == "ItemTail" and not lado_der:
        return {"tipo": "itemtail", "items": []}

    if hijos:
        return hijos[0]
    return crear_valor("")


def closure(items, producciones_por_nt, no_terminales, first):

    cerradura = set(items)
    cambio = True

    while cambio:
        cambio = False
        nuevos_items = set()

        for item in cerradura:
            simbolo = item.simbolo_despues_punto()

            if simbolo not in no_terminales:
                continue

            beta = list(item.lado_der[item.punto + 1 :])
            beta.append(item.anticipacion)
            primeros = calcular_first_cadena(beta, first) - {EPSILON}

            for produccion in producciones_por_nt[simbolo]:
                for anticipacion in primeros:
                    nuevo_item = ItemLR1(simbolo, tuple(produccion), 0, anticipacion)
                    if nuevo_item not in cerradura:
                        nuevos_items.add(nuevo_item)

        if nuevos_items:
            cerradura.update(nuevos_items)
            cambio = True

    return frozenset(cerradura)


def ir_a(items, simbolo, producciones_por_nt, no_terminales, first):

    movidos = set()

    for item in items:
        if item.simbolo_despues_punto() == simbolo:
            movidos.add(item.avanzar_punto())

    if not movidos:
        return frozenset()

    return closure(movidos, producciones_por_nt, no_terminales, first)


def coleccion_canonica_lr1(terminales, no_terminales, inicial, producciones, first):

    producciones_por_nt = agrupar_producciones(producciones)
    simbolos = list(terminales) + list(no_terminales)

    item_inicial = ItemLR1(inicial, tuple(producciones_por_nt[inicial][0]), 0, EOF)
    estado_inicial = closure({item_inicial}, producciones_por_nt, no_terminales, first)

    estados = [estado_inicial]
    transiciones = {}
    pendientes = [estado_inicial]

    while pendientes:
        estado = pendientes.pop(0)
        indice_estado = estados.index(estado)

        for simbolo in simbolos:
            destino = ir_a(estado, simbolo, producciones_por_nt, no_terminales, first)
            if not destino:
                continue

            if destino not in estados:
                estados.append(destino)
                pendientes.append(destino)

            indice_destino = estados.index(destino)
            transiciones[(indice_estado, simbolo)] = indice_destino

    return estados, transiciones


def enumerar_producciones(producciones):

    enumeradas = []

    for indice, (lado_izq, lado_der) in enumerate(producciones):
        enumeradas.append(
            {
                "indice": indice,
                "lado_izq": lado_izq,
                "lado_der": list(lado_der),
            }
        )

    return enumeradas


def construir_tabla_lr1(
    estados, transiciones, terminales, no_terminales, producciones, inicial_aumentado
):

    action = {}
    goto = {}
    conflictos = []
    # (lado_izq, lado_der) -> numero de produccion
    mapa_producciones = {
        (lado_izq, tuple(lado_der)): indice
        for indice, (lado_izq, lado_der) in enumerate(producciones)
    }

    def registrar_accion(estado, simbolo, valor):
        # Si una misma celda ACTION recibe dos valores distintos,
        # guardamos el conflicto para poder reportarlo.
        clave = (estado, simbolo)
        if clave in action and action[clave] != valor:
            conflictos.append((clave, action[clave], valor))
        action[clave] = valor

    # 1:
    for (estado, simbolo), destino in transiciones.items():
        if simbolo in terminales:
            registrar_accion(estado, simbolo, ("shift", destino))
        elif simbolo in no_terminales:
            goto[(estado, simbolo)] = destino

    # 2:
    for indice_estado, estado in enumerate(estados):
        for item in estado:
            if not item.completado():
                continue

            # inicial_aumentado -> inicial ., $
            if item.lado_izq == inicial_aumentado and item.anticipacion == EOF:
                registrar_accion(indice_estado, EOF, ("accept",))
                continue

            # entonces ACTION[estado, a] = reduce A -> alpha
            numero_produccion = mapa_producciones[(item.lado_izq, item.lado_der)]
            registrar_accion(
                indice_estado, item.anticipacion, ("reduce", numero_produccion)
            )

    return action, goto, conflictos


def ordenar_no_terminales_recuperacion(no_terminales):

    prioridad = [
        "StmtList",
        "Stmt",
        "DocStmt",
        "Expr",
        "ExprTail",
        "Term",
        "Factor",
        "FuncCall",
        "Literal",
        "ItemList",
        "ItemTail",
        "Program",
    ]

    ordenados = [nt for nt in prioridad if nt in no_terminales]
    ordenados.extend(nt for nt in no_terminales if nt not in ordenados)
    return ordenados


def recuperar_en_parser_lr1(
    pila_estados,
    pila_simbolos,
    pila_nodos,
    pila_semantica,
    goto,
    entrada,
    indice_entrada,
    no_terminales_recuperacion,
    sincronizacion_por_nt,
):

    while pila_estados:
        estado_actual = pila_estados[-1]

        for no_terminal in no_terminales_recuperacion:
            estado_destino = goto.get((estado_actual, no_terminal))
            if estado_destino is None:
                continue

            sincronizadores = sincronizacion_por_nt.get(no_terminal, {EOF})
            while (
                indice_entrada < len(entrada)
                and entrada[indice_entrada] not in sincronizadores
                and entrada[indice_entrada] != EOF
            ):
                indice_entrada += 1

            pila_simbolos.append(no_terminal)
            pila_estados.append(estado_destino)
            pila_nodos.append(NodoParseo(no_terminal, [NodoParseo("<error>", [])]))
            pila_semantica.append(
                crear_valor(
                    "",
                    "<span class='identifier unresolved'>&lt;error&gt;</span>",
                    extra={"error": True},
                )
            )

            return {
                "recuperado": True,
                "indice_entrada": indice_entrada,
                "no_terminal": no_terminal,
                "sincronizadores": sorted(list(sincronizadores)),
                "estado_destino": estado_destino,
            }

        pila_estados.pop()
        if pila_simbolos:
            pila_simbolos.pop()
        if pila_nodos:
            pila_nodos.pop()
        if pila_semantica:
            pila_semantica.pop()

    return {
        "recuperado": False,
        "indice_entrada": indice_entrada,
        "no_terminal": None,
        "sincronizadores": [],
        "estado_destino": None,
    }


def parsear_lr1(
    action,
    goto,
    producciones,
    tokens,
    tokens_semanticos=None,
    no_terminales_recuperacion=None,
    sincronizacion_por_nt=None,
):

    entrada = list(tokens) + [EOF]
    tokens_semanticos = list(tokens_semanticos or [])
    pila_estados = [0]
    pila_simbolos = []
    pila_nodos = []
    pila_semantica = []
    historial = []
    errores = []
    recuperado = False
    indice_entrada = 0
    contexto_traduccion = crear_contexto_traduccion()

    while True:
        estado = pila_estados[-1]
        token_actual = entrada[indice_entrada]
        accion = action.get((estado, token_actual))

        historial.append(
            {
                "pila_estados": list(pila_estados),
                "pila_simbolos": list(pila_simbolos),
                "entrada": entrada[indice_entrada:],
                "accion": formatear_accion_corta(accion),
            }
        )

        if accion is None:
            mensaje = f"No hay accion para estado {estado} con simbolo {token_actual}"
            errores.append(
                {
                    "tipo": "no_action",
                    "estado": estado,
                    "token": token_actual,
                    "mensaje": mensaje,
                    "indice_entrada": indice_entrada,
                }
            )

            if not no_terminales_recuperacion or not sincronizacion_por_nt:
                return {
                    "aceptada": False,
                    "error": mensaje,
                    "pasos": historial,
                    "arbol": None,
                    "errores": errores,
                    "recuperado": recuperado,
                    "traduccion": construir_documento_traducido(
                        {"items": []},
                        contexto_traduccion,
                    ),
                }

            resultado_recuperacion = recuperar_en_parser_lr1(
                pila_estados,
                pila_simbolos,
                pila_nodos,
                pila_semantica,
                goto,
                entrada,
                indice_entrada,
                no_terminales_recuperacion,
                sincronizacion_por_nt,
            )

            if resultado_recuperacion["recuperado"]:
                recuperado = True
                indice_entrada = resultado_recuperacion["indice_entrada"]
                historial.append(
                    {
                        "info": "recuperacion",
                        "mensaje": (
                            f"Se recupero con el no terminal "
                            f"{resultado_recuperacion['no_terminal']} "
                            f"hacia el estado {resultado_recuperacion['estado_destino']} "
                            f"sincronizando con "
                            f"{resultado_recuperacion['sincronizadores']}. "
                            f"Error: {mensaje}"
                        ),
                    }
                )
                continue

            return {
                "aceptada": False,
                "error": mensaje,
                "pasos": historial,
                "arbol": None,
                "errores": errores,
                "recuperado": recuperado,
                "traduccion": construir_documento_traducido(
                    {"items": []},
                    contexto_traduccion,
                ),
            }

        if accion[0] == "shift":
            destino = accion[1]
            pila_simbolos.append(token_actual)
            pila_estados.append(destino)
            pila_nodos.append(NodoParseo(token_actual, []))
            if indice_entrada < len(tokens_semanticos):
                pila_semantica.append(crear_token_semantico(tokens_semanticos[indice_entrada]))
            else:
                pila_semantica.append(crear_token_semantico(token_actual))
            indice_entrada += 1
            continue

        if accion[0] == "reduce":
            indice_produccion = accion[1]
            lado_izq, lado_der = producciones[indice_produccion]
            cantidad = len(lado_der)

            hijos = []
            hijos_semanticos = []
            for _ in range(cantidad):
                pila_simbolos.pop()
                pila_estados.pop()
                hijos.append(pila_nodos.pop())
                hijos_semanticos.append(pila_semantica.pop())

            hijos.reverse()
            hijos_semanticos.reverse()
            if not lado_der:
                hijos = [NodoParseo(EPSILON, [])]
                hijos_semanticos = []

            nuevo_nodo = NodoParseo(lado_izq, hijos)
            valor_semantico = aplicar_accion_semantica(
                indice_produccion,
                lado_izq,
                lado_der,
                hijos_semanticos,
                contexto_traduccion,
            )
            estado_destino = goto.get((pila_estados[-1], lado_izq))

            if estado_destino is None:
                return {
                    "aceptada": False,
                    "error": f"No hay goto para estado {pila_estados[-1]} con simbolo {lado_izq}",
                    "pasos": historial,
                    "arbol": None,
                    "errores": errores,
                    "recuperado": recuperado,
                    "traduccion": construir_documento_traducido(
                        {"items": []},
                        contexto_traduccion,
                    ),
                }

            pila_simbolos.append(lado_izq)
            pila_estados.append(estado_destino)
            pila_nodos.append(nuevo_nodo)
            pila_semantica.append(valor_semantico)
            continue

        if accion[0] == "accept":
            raiz = pila_nodos[-1] if pila_nodos else None
            programa = pila_semantica[-1] if pila_semantica else {"items": []}
            return {
                "aceptada": True,
                "error": None,
                "pasos": historial,
                "arbol": raiz.a_dict() if raiz else None,
                "errores": errores,
                "recuperado": recuperado,
                "traduccion": construir_documento_traducido(
                    programa if isinstance(programa, dict) else {"items": []},
                    contexto_traduccion,
                ),
            }


def formatear_accion(accion, producciones):

    if accion is None:
        return "error"

    if accion[0] == "shift":
        return f"shift {accion[1]}"

    if accion[0] == "reduce":
        lado_izq, lado_der = producciones[accion[1]]
        return f"reduce {formatear_produccion(lado_izq, lado_der)}"

    return "accept"


def formatear_accion_corta(accion):

    if accion is None:
        return ""

    if accion[0] == "shift":
        return f"s{accion[1]}"

    if accion[0] == "reduce":
        return f"r{accion[1]}"

    return "acc"


def serializar_first(first):

    return {simbolo: sorted(list(valores)) for simbolo, valores in first.items()}


def serializar_follow(follow):

    return {simbolo: sorted(list(valores)) for simbolo, valores in follow.items()}


def serializar_estados(estados, simbolo_inicial_aumentado=None):

    resultado = []
    for indice, estado in enumerate(estados):
        agrupados = {}
        for item in estado:
            clave = item.nucleo()
            if clave not in agrupados:
                agrupados[clave] = {
                    "texto_base": item.texto_sin_lookahead(),
                    "lookaheads": set(),
                    "punto": item.punto,
                }
            agrupados[clave]["lookaheads"].add(item.anticipacion)

        def clave_orden_item(par):
            lhs, rhs, punto = par[0]
            prioridad_inicial = (
                0
                if simbolo_inicial_aumentado is not None
                and lhs == simbolo_inicial_aumentado
                else 1
            )
            return (prioridad_inicial, lhs, rhs, punto)

        items_agrupados = []
        for _, info in sorted(agrupados.items(), key=clave_orden_item):
            lookaheads = sorted(info["lookaheads"])
            items_agrupados.append(
                {
                    "texto": f"{info['texto_base']}, {formatear_lookaheads(lookaheads)}",
                    "punto": info["punto"],
                }
            )

        resultado.append(
            {
                "indice": indice,
                "items": [item["texto"] for item in items_agrupados],
                "kernel": [
                    item["texto"] for item in items_agrupados if item["punto"] > 0
                ]
                or ["-"],
            }
        )

    return resultado


def serializar_transiciones(transiciones):

    resultado = []
    for (estado, simbolo), destino in sorted(transiciones.items()):
        resultado.append(
            {
                "desde": estado,
                "simbolo": simbolo,
                "hacia": destino,
            }
        )

    return resultado


def serializar_tabla(
    action, goto, terminales, no_terminales, total_estados, producciones
):

    filas = []

    for estado in range(total_estados):
        fila_action = {}
        fila_goto = {}

        for terminal in terminales + [EOF]:
            accion = action.get((estado, terminal))
            if accion is not None:
                fila_action[terminal] = formatear_accion_corta(accion)

        for no_terminal in no_terminales:
            destino = goto.get((estado, no_terminal))
            if destino is not None:
                fila_goto[no_terminal] = destino

        filas.append(
            {
                "estado": estado,
                "action": fila_action,
                "goto": fila_goto,
            }
        )

    return filas


def construir_demo_lr1(ruta_gramatica, tokens_entrada):

    terminales, no_terminales, inicial, producciones = leer_gramatica(ruta_gramatica)
    return construir_demo_lr1_desde_componentes(
        terminales, no_terminales, inicial, producciones, tokens_entrada
    )


def construir_demo_lr1_desde_fuente(ruta_gramatica, texto_fuente):

    terminales, no_terminales, inicial, producciones = leer_gramatica(ruta_gramatica)
    return construir_demo_lr1_desde_componentes_con_scanner(
        terminales, no_terminales, inicial, producciones, texto_fuente
    )


def construir_demo_lr1_desde_texto(texto_gramatica, tokens_entrada):

    terminales, no_terminales, inicial, producciones = leer_gramatica_desde_texto(
        texto_gramatica
    )
    return construir_demo_lr1_desde_componentes(
        terminales,
        no_terminales,
        inicial,
        producciones,
        tokens_entrada,
        texto_gramatica,
    )


def construir_demo_lr1_desde_texto_y_fuente(texto_gramatica, texto_fuente):

    terminales, no_terminales, inicial, producciones = leer_gramatica_desde_texto(
        texto_gramatica
    )
    return construir_demo_lr1_desde_componentes_con_scanner(
        terminales,
        no_terminales,
        inicial,
        producciones,
        texto_fuente,
        texto_gramatica,
    )


def construir_demo_lr1_desde_componentes(
    terminales,
    no_terminales,
    inicial,
    producciones,
    tokens_entrada,
    tokens_semanticos=None,
    texto_fuente_original=None,
):

    first = calcular_first(terminales, no_terminales, producciones)
    follow = calcular_follow(no_terminales, producciones, inicial, first)

    inicial_aumentado, no_terminales_aumentados, producciones_aumentadas = (
        aumentar_gramatica(inicial, no_terminales, producciones)
    )
    first_aumentado = calcular_first(
        terminales, no_terminales_aumentados, producciones_aumentadas
    )
    estados, transiciones = coleccion_canonica_lr1(
        terminales,
        no_terminales_aumentados,
        inicial_aumentado,
        producciones_aumentadas,
        first_aumentado,
    )
    action, goto, conflictos = construir_tabla_lr1(
        estados,
        transiciones,
        terminales,
        no_terminales_aumentados,
        producciones_aumentadas,
        inicial_aumentado,
    )
    no_terminales_recuperacion = ordenar_no_terminales_recuperacion(no_terminales)
    sincronizacion_por_nt = {
        nt: set(follow.get(nt, {EOF})) | {EOF}
        for nt in no_terminales_recuperacion
    }
    parseo = parsear_lr1(
        action,
        goto,
        producciones_aumentadas,
        tokens_entrada,
        tokens_semanticos,
        no_terminales_recuperacion,
        sincronizacion_por_nt,
    )

    return {
        "gramatica": {
            "terminales": terminales,
            "no_terminales": no_terminales,
            "inicial": inicial,
            "producciones": [
                formatear_produccion(lado_izq, lado_der)
                for lado_izq, lado_der in producciones
            ],
            "inicial_aumentado": inicial_aumentado,
            "producciones_aumentadas": [
                formatear_produccion(lado_izq, lado_der)
                for lado_izq, lado_der in producciones_aumentadas
            ],
            "texto_fuente": formatear_gramatica_fuente(
                producciones_aumentadas,
                texto_fuente_original,
            ),
        },
        "first": serializar_first(first_aumentado),
        "follow": serializar_follow(follow),
        "estados": serializar_estados(estados, inicial_aumentado),
        "transiciones": serializar_transiciones(transiciones),
        "tabla": serializar_tabla(
            action,
            goto,
            terminales,
            no_terminales_aumentados,
            len(estados),
            producciones_aumentadas,
        ),
        "conflictos": [
            {
                "estado": clave[0],
                "simbolo": clave[1],
                "existente": formatear_accion_corta(vieja),
                "nuevo": formatear_accion_corta(nueva),
            }
            for clave, vieja, nueva in conflictos
        ],
        "parseo": parseo,
        "traduccion": parseo.get("traduccion", {}),
        "panic_mode": {
            "no_terminales_recuperacion": no_terminales_recuperacion,
            "sincronizacion_por_nt": {
                nt: sorted(list(simbolos))
                for nt, simbolos in sincronizacion_por_nt.items()
            },
        },
        "scanner": {
            "fuente": "",
            "tokens": [],
            "errores": [],
            "traza": [],
        },
        "producciones_enumeradas": enumerar_producciones(producciones_aumentadas),
        "entrada": list(tokens_entrada) + [EOF],
        "entrada_lexica": list(tokens_entrada),
    }


def construir_demo_lr1_desde_componentes_con_scanner(
    terminales,
    no_terminales,
    inicial,
    producciones,
    texto_fuente,
    texto_fuente_original=None,
):

    resultado_scanner = escanear_fuente(texto_fuente)
    tokens_scanner = resultado_scanner["tokens"]
    tokens_parser = [
        token["tipo"]
        for token in tokens_scanner
        if token["tipo"] != SCANNER_EOF
    ]

    datos = construir_demo_lr1_desde_componentes(
        terminales,
        no_terminales,
        inicial,
        producciones,
        tokens_parser,
        tokens_scanner,
        texto_fuente_original,
    )

    datos["scanner"] = {
        "fuente": texto_fuente,
        "tokens": tokens_scanner,
        "errores": resultado_scanner["errores"],
        "traza": resultado_scanner["traza"],
    }
    datos["entrada_lexica"] = tokens_parser
    return datos


def formatear_gramatica_fuente(producciones_aumentadas, texto_fuente_original=None):

    if texto_fuente_original and "TERMINALES:" in texto_fuente_original:
        return texto_fuente_original.strip()

    lineas = []
    for lado_izq, lado_der in producciones_aumentadas:
        if lado_der:
            lineas.append(f"{lado_izq} -> {' '.join(lado_der)}")
        else:
            lineas.append(f"{lado_izq} -> {EPSILON}")

    return "\n".join(lineas)


def parsear_desde_gramatica(ruta_gramatica, tokens_entrada):

    datos = construir_demo_lr1(ruta_gramatica, tokens_entrada)
    return {
        "entrada": datos["entrada"],
        "parseo": datos["parseo"],
    }


def imprimir_resumen_demo(datos):

    print("FIRST:")
    for simbolo, valores in datos["first"].items():
        print(simbolo, "=", valores)

    print("\nEstados LR(1):")
    for estado in datos["estados"]:
        print(f"I{estado['indice']}:")
        for item in estado["items"]:
            print(" ", item)
        print()

    print("Tabla LR(1):")
    for fila in datos["tabla"]:
        print(f"Estado {fila['estado']}: ACTION={fila['action']} GOTO={fila['goto']}")

    print("\nParseo:")
    for paso in datos["parseo"]["pasos"]:
        print(paso)

    print("\nAceptada:", datos["parseo"]["aceptada"])
    if datos["parseo"]["error"]:
        print("Error:", datos["parseo"]["error"])


if __name__ == "__main__":
    demo = construir_demo_lr1_desde_fuente(
        "gramatica.txt",
        'titulo = upper("Mini Latex"); section(titulo); paragraph("Hola " + color("verde", "mundo") + "."); itemize(item("uno"), item(color("verde", "dos")));',
    )
    imprimir_resumen_demo(demo)
    print("\nJSON:")
    print(json.dumps(demo, ensure_ascii=False, indent=2))
