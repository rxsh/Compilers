from dataclasses import dataclass
import json


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
        inicial, producciones = quitar_produccion_aumentada_si_existe(producciones, no_terminales)
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
        raise ValueError("La gramatica debe declarar INICIAL o tener una produccion inicial")
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
                raise ValueError(f"El simbolo '{simbolo}' no esta declarado como terminal o no terminal")

    return terminales, no_terminales, inicial, producciones


def parsear_linea_produccion(linea, numero_linea):

    if "->" not in linea:
        raise ValueError(f"Produccion invalida en linea {numero_linea}: falta '->'")

    lado_izq, lado_der = linea.split("->", 1)
    lado_izq = lado_izq.strip()
    if not lado_izq:
        raise ValueError(f"Produccion invalida en linea {numero_linea}: falta lado izquierdo")

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

            beta = list(item.lado_der[item.punto + 1:])
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
        enumeradas.append({
            "indice": indice,
            "lado_izq": lado_izq,
            "lado_der": list(lado_der),
        })

    return enumeradas


def construir_tabla_lr1(estados, transiciones, terminales, no_terminales, producciones, inicial_aumentado):

    action = {}
    goto = {}
    conflictos = []
    # Mapa de apoyo:
    # (lado_izq, lado_der) -> numero de produccion
    # Esto nos deja saber rapidamente que reduccion registrar en ACTION.
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

    # Paso 1:
    # Las transiciones del automata llenan:
    # - ACTION con "shift" si la transicion es con un terminal
    # - GOTO si la transicion es con un no terminal
    for (estado, simbolo), destino in transiciones.items():
        if simbolo in terminales:
            registrar_accion(estado, simbolo, ("shift", destino))
        elif simbolo in no_terminales:
            goto[(estado, simbolo)] = destino

    # Paso 2:
    # Todo item con el punto al final produce una accion.
    # Puede ser:
    # - accept, si es el item inicial aumentado con lookahead $
    # - reduce, usando el lookahead exacto del item LR(1)
    for indice_estado, estado in enumerate(estados):
        for item in estado:
            if not item.completado():
                continue

            # Caso de aceptacion:
            # inicial_aumentado -> inicial ., $
            if item.lado_izq == inicial_aumentado and item.anticipacion == EOF:
                registrar_accion(indice_estado, EOF, ("accept",))
                continue

            # Caso de reduccion:
            # A -> alpha ., a
            # entonces ACTION[estado, a] = reduce A -> alpha
            numero_produccion = mapa_producciones[(item.lado_izq, item.lado_der)]
            registrar_accion(indice_estado, item.anticipacion, ("reduce", numero_produccion))

    return action, goto, conflictos


def parsear_lr1(action, goto, producciones, tokens):

    entrada = list(tokens) + [EOF]
    pila_estados = [0]
    pila_simbolos = []
    pila_nodos = []
    historial = []
    indice_entrada = 0

    while True:
        estado = pila_estados[-1]
        token_actual = entrada[indice_entrada]
        accion = action.get((estado, token_actual))

        historial.append({
            "pila_estados": list(pila_estados),
            "pila_simbolos": list(pila_simbolos),
            "entrada": entrada[indice_entrada:],
            "accion": formatear_accion_corta(accion),
        })

        if accion is None:
            return {
                "aceptada": False,
                "error": f"No hay accion para estado {estado} con simbolo {token_actual}",
                "pasos": historial,
                "arbol": None,
            }

        if accion[0] == "shift":
            destino = accion[1]
            pila_simbolos.append(token_actual)
            pila_estados.append(destino)
            pila_nodos.append(NodoParseo(token_actual, []))
            indice_entrada += 1
            continue

        if accion[0] == "reduce":
            indice_produccion = accion[1]
            lado_izq, lado_der = producciones[indice_produccion]
            cantidad = len(lado_der)

            hijos = []
            for _ in range(cantidad):
                pila_simbolos.pop()
                pila_estados.pop()
                hijos.append(pila_nodos.pop())

            hijos.reverse()
            if not lado_der:
                hijos = [NodoParseo(EPSILON, [])]

            nuevo_nodo = NodoParseo(lado_izq, hijos)
            estado_destino = goto.get((pila_estados[-1], lado_izq))

            if estado_destino is None:
                return {
                    "aceptada": False,
                    "error": f"No hay goto para estado {pila_estados[-1]} con simbolo {lado_izq}",
                    "pasos": historial,
                    "arbol": None,
                }

            pila_simbolos.append(lado_izq)
            pila_estados.append(estado_destino)
            pila_nodos.append(nuevo_nodo)
            continue

        if accion[0] == "accept":
            raiz = pila_nodos[-1] if pila_nodos else None
            return {
                "aceptada": True,
                "error": None,
                "pasos": historial,
                "arbol": raiz.a_dict() if raiz else None,
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
            prioridad_inicial = 0 if simbolo_inicial_aumentado is not None and lhs == simbolo_inicial_aumentado else 1
            return (prioridad_inicial, lhs, rhs, punto)

        items_agrupados = []
        for _, info in sorted(agrupados.items(), key=clave_orden_item):
            lookaheads = sorted(info["lookaheads"])
            items_agrupados.append({
                "texto": f"{info['texto_base']}, {formatear_lookaheads(lookaheads)}",
                "punto": info["punto"],
            })

        resultado.append({
            "indice": indice,
            "items": [item["texto"] for item in items_agrupados],
            "kernel": [item["texto"] for item in items_agrupados if item["punto"] > 0] or ["-"],
        })

    return resultado


def serializar_transiciones(transiciones):

    resultado = []
    for (estado, simbolo), destino in sorted(transiciones.items()):
        resultado.append({
            "desde": estado,
            "simbolo": simbolo,
            "hacia": destino,
        })

    return resultado


def serializar_tabla(action, goto, terminales, no_terminales, total_estados, producciones):

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

        filas.append({
            "estado": estado,
            "action": fila_action,
            "goto": fila_goto,
        })

    return filas


def construir_demo_lr1(ruta_gramatica, tokens_entrada):

    terminales, no_terminales, inicial, producciones = leer_gramatica(ruta_gramatica)
    return construir_demo_lr1_desde_componentes(terminales, no_terminales, inicial, producciones, tokens_entrada)


def construir_demo_lr1_desde_texto(texto_gramatica, tokens_entrada):

    terminales, no_terminales, inicial, producciones = leer_gramatica_desde_texto(texto_gramatica)
    return construir_demo_lr1_desde_componentes(
        terminales,
        no_terminales,
        inicial,
        producciones,
        tokens_entrada,
        texto_gramatica,
    )


def construir_demo_lr1_desde_componentes(
    terminales,
    no_terminales,
    inicial,
    producciones,
    tokens_entrada,
    texto_fuente_original=None,
):

    first = calcular_first(terminales, no_terminales, producciones)
    follow = calcular_follow(no_terminales, producciones, inicial, first)

    inicial_aumentado, no_terminales_aumentados, producciones_aumentadas = aumentar_gramatica(
        inicial, no_terminales, producciones
    )
    first_aumentado = calcular_first(terminales, no_terminales_aumentados, producciones_aumentadas)
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
    parseo = parsear_lr1(action, goto, producciones_aumentadas, tokens_entrada)

    return {
        "gramatica": {
            "terminales": terminales,
            "no_terminales": no_terminales,
            "inicial": inicial,
            "producciones": [
                formatear_produccion(lado_izq, lado_der) for lado_izq, lado_der in producciones
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
        "producciones_enumeradas": enumerar_producciones(producciones_aumentadas),
        "entrada": list(tokens_entrada) + [EOF],
    }


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

    demo = construir_demo_lr1("gramatica.txt", ["x", "x", "y", "y"])
    imprimir_resumen_demo(demo)
    print("\nJSON:")
    print(json.dumps(demo, ensure_ascii=False, indent=2))
