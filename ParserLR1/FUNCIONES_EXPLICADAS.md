# Explicaciones línea a línea — Funciones clave (resumen rápido)

Este archivo resume, de forma concisa y "línea a línea" cuando procede, cómo funcionan las funciones que debes presentar hoy. Está pensado para lectura rápida antes de la exposición.

---

## tokenizar_lista(texto)
- `tokens = []` — lista de salida.
- `for t in texto.split():` — divide la cadena por espacios y recorre cada pedazo.
- `if t == "()":` — caso especial: si aparece "()" como token conjunto.
  - `tokens.append("(")` y `tokens.append(")")` — lo separa en paréntesis abiertos y cerrados.
- `else: tokens.append(t)` — añade el token tal cual.
- `return tokens` — devuelve la lista de tokens.

Propósito: convertir la línea de terminales/no terminales en una lista Python usable.

---

## leer_gramatica(ruta)
- Inicializaciones:
  - `producciones = []`, `terminales = []`, `no_terminales = []`, `inicial = None`, `en_producciones = False`.
- `with open(ruta, "r", encoding="UTF-8") as f:` — abre el archivo de gramática.
- `for linea in f:` — itera cada línea del archivo.
  - `linea = linea.strip()` — eliminar espacios al inicio/fin.
  - `if not linea or linea.startswith("#"): continue` — ignora líneas vacías y comentarios.
  - Si `linea.startswith("TERMINALES:")`:
    - `datos = linea.split(":", 1)[1].strip()` — toma la parte después de `:`.
    - `terminales = tokenizar_lista(datos)` — convierte a lista de símbolos.
    - `en_producciones = False` y `continue`.
  - Si `linea.startswith("NO_TERMINALES:")` — análogo para no terminales.
  - Si `linea.startswith("INICIAL:")`:
    - `inicial = linea.split(":", 1)[1].strip()` — guarda símbolo inicial.
  - Si `linea.startswith("PRODUCCIONES:")`:
    - `en_producciones = True` y `continue`.
  - Si `en_producciones`:
    - `lado_izq, lado_der = linea.split("->")` — separa LHS y RHS.
    - `lado_izq = lado_izq.strip()` — limpia LHS.
    - `alternativas = lado_der.split("|")` — maneja `A -> alpha | beta`.
    - Para cada `alt` en `alternativas`:
      - `simbolos_der = alt.strip().split()` — divide RHS en símbolos.
      - `if simbolos_der == [EPSILON]: simbolos_der = []` — representa epsilon como lista vacía.
      - `producciones.append((lado_izq, simbolos_der))` — añade la producción.
- `return terminales, no_terminales, inicial, producciones` — estructura final.

Nota: las producciones se guardan como `("A", ["x", "y"])` o `("Ep", [])` para epsilon.

---

## calcular_first(terminales, no_terminales, producciones)
Objetivo: construir `FIRST` para todos los símbolos (terminales, no terminales y ε).

- `first = {}` — mapa símbolo -> conjunto.
- Para cada terminal `t` y `EOF`: `first[t] = {t}` — los terminales tienen su propio FIRST.
- `first[EPSILON] = {EPSILON}` — ε contiene ε.
- Para cada `nt` en `no_terminales`: `first[nt] = set()` — inicializa vacíos.
- Bucle `while cambio:` para fijo iterativo:
  - `for A, B in producciones:` — por cada producción A -> B.
  - `rhs = set()` — conjunto temporal para acumular FIRST(B).
  - `i = 0` y si `not B: rhs.add(EPSILON)` — si RHS es vacío, FIRST contiene ε.
  - `while i < len(B):` — procesa símbolos de B de izquierda a derecha:
    - `simbolo = B[i]`
    - `rhs.update(first[simbolo] - {EPSILON})` — agrega terminales alcanzables inicialmente.
    - `if EPSILON in first[simbolo]: i += 1` — si símbolo puede producir ε, seguir al siguiente.
    - `else: break` — si no, parar.
  - `if B and i == len(B): rhs.add(EPSILON)` — si todos los símbolos derivan ε, agregar ε.
  - `before = len(first[A]); first[A].update(rhs)` — actualizar FIRST(A).
  - Si creció, marcar `cambio = True` para otra iteración.
- `return first`.

Observación: es el algoritmo clásico de cierre por iteración hasta estabilidad.

---

## calcular_first_cadena(cadena, first)
Calcula FIRST para una secuencia de símbolos (útil dentro de `closure`).

- Si `not cadena`: `return {EPSILON}` — FIRST(vacío) = {ε}.
- `resultado = set(); i = 0`.
- Mientras `i < len(cadena)`:
  - `simbolo = cadena[i]`
  - `resultado.update(first[simbolo] - {EPSILON})` — agrega terminales iniciales.
  - Si `EPSILON in first[simbolo]`: `i += 1` y continuar; si no, `break`.
- Si `i == len(cadena)`: `resultado.add(EPSILON)` — todos podían producir ε.
- `return resultado`.

Uso clave: en LR(1) se usa para `FIRST(β a)` cuando cierres items `A -> α · B β, a`.

---

## closure(items, producciones_por_nt, no_terminales, first)
Pasos (línea a línea conceptual):
- `cerradura = set(items)` — empieza con los items dados.
- `cambio = True` y bucle hasta estabilizar.
- Para cada `item` en `cerradura`:
  - `simbolo = item.simbolo_despues_punto()` — símbolo justo después del punto.
  - `if simbolo not in no_terminales: continue` — solo nos interesan no terminales.
  - `beta = list(item.lado_der[item.punto + 1:])` — resto después de B.
  - `beta.append(item.anticipacion)` — añadimos el lookahead `a` al final.
  - `primeros = calcular_first_cadena(beta, first) - {EPSILON}` — FIRST(β a) salvo ε.
  - Por cada `produccion` en `producciones_por_nt[simbolo]`:
    - Por cada `anticipacion` en `primeros`:
      - `nuevo_item = ItemLR1(simbolo, tuple(produccion), 0, anticipacion)` — B -> · γ, b
      - Si `nuevo_item` no está en `cerradura`, agrégalo a `nuevos_items`.
- Si `nuevos_items` no está vacío: `cerradura.update(nuevos_items)` y repetir.
- `return frozenset(cerradura)` — devuelve conjunto inmutable (estado).

Importante: los lookaheads se calculan con FIRST de la secuencia que sigue al no terminal más el lookahead del item original.

---

## ir_a(items, simbolo, producciones_por_nt, no_terminales, first)
Implementa `goto(I, X)`:
- `movidos = set()` — contenedor temporal.
- Para cada `item` en `items`:
  - Si `item.simbolo_despues_punto() == simbolo`: `movidos.add(item.avanzar_punto())`.
- Si `not movidos`: `return frozenset()` — goto vacío.
- Si hay movidos: `return closure(movidos, producciones_por_nt, no_terminales, first)`.

---

## coleccion_canonica_lr1(terminales, no_terminales, inicial, producciones, first)
Resumen rápido de pasos:
1. `producciones_por_nt = agrupar_producciones(producciones)` — accesos rápidos por LHS.
2. `simbolos = list(terminales) + list(no_terminales)` — símbolos que generan aristas.
3. `item_inicial = ItemLR1(inicial, tuple(producciones_por_nt[inicial][0]), 0, EOF)` — S' -> · S, $
4. `estado_inicial = closure({item_inicial}, ...)` y `estados = [estado_inicial]`, `pendientes = [estado_inicial]`.
5. Mientras `pendientes` no vacío:
   - `estado = pendientes.pop(0)` y `indice_estado = estados.index(estado)`.
   - Para cada `simbolo` en `simbolos`:
     - `destino = ir_a(estado, simbolo, ...)`.
     - Si `destino` vacío: continuar.
     - Si `destino` no está en `estados`: añadir a `estados` y `pendientes`.
     - `transiciones[(indice_estado, simbolo)] = indice_destino`.
6. `return estados, transiciones`.

Observación: la representación de `estado` es un `frozenset` de items, por eso se puede comparar e indexar.

---

## construir_tabla_lr1(estados, transiciones, terminales, no_terminales, producciones, inicial_aumentado)
Puntos clave:
- `mapa_producciones` convierte `(lado_izq, tuple(lado_der))` -> índice de producción.
- `registrar_accion(estado, simbolo, valor)` guarda en `action` y detecta conflictos.

Paso 1 (shifts/gotos):
- Para cada `(estado, simbolo) -> destino` en `transiciones`:
  - Si `simbolo in terminales`: `ACTION[estado, simbolo] = ('shift', destino)`.
  - Si `simbolo in no_terminales`: `GOTO[estado, simbolo] = destino`.

Paso 2 (reducciones y accept):
- Para cada `indice_estado, estado` en `estados`:
  - Para cada `item` en `estado`:
    - Si `item.completado()`:
      - Si `item.lado_izq == inicial_aumentado and item.anticipacion == EOF`: `ACTION[estado, $] = ('accept',)`.
      - Sino: `numero_produccion = mapa_producciones[(item.lado_izq, item.lado_der)]` y `ACTION[estado, item.anticipacion] = ('reduce', numero_produccion)`.

Salida: `action, goto, conflictos`.

---

## parsear_lr1(action, goto, producciones, tokens)
Algoritmo LR(1) con trazabilidad y construcción de árbol:

- `entrada = list(tokens) + [EOF]` — tokens más marcador final.
- `pila_estados = [0]`, `pila_simbolos = []`, `pila_nodos = []`, `historial = []`, `indice_entrada = 0`.
- Bucle principal:
  - `estado = pila_estados[-1]`, `token_actual = entrada[indice_entrada]`.
  - `accion = action.get((estado, token_actual))`.
  - Guardar paso en `historial` con `formatear_accion_corta(accion)`.
  - Si `accion is None`: error y retorno con historial.
  - `if accion[0] == 'shift'`:
    - `destino = accion[1]`, push `token_actual` en `pila_simbolos`, push `destino` en `pila_estados`.
    - `pila_nodos.append(NodoParseo(token_actual, []))` — nodo hoja para token.
    - `indice_entrada += 1` y `continue`.
  - `if accion[0] == 'reduce'`:
    - `indice_produccion = accion[1]`, `lado_izq, lado_der = producciones[indice_produccion]`.
    - `cantidad = len(lado_der)`.
    - Pop `cantidad` veces de `pila_simbolos`, `pila_estados` y `pila_nodos` para reunir hijos.
    - `hijos.reverse()` — orden correcto.
    - Si `not lado_der`: `hijos = [NodoParseo(EPSILON, [])]`.
    - `nuevo_nodo = NodoParseo(lado_izq, hijos)`.
    - `estado_destino = goto.get((pila_estados[-1], lado_izq))` — busca goto.
    - Si `estado_destino is None`: error.
    - Push `lado_izq` en `pila_simbolos`, `estado_destino` en `pila_estados`, `nuevo_nodo` en `pila_nodos`.
    - `continue`.
  - `if accion[0] == 'accept'`: construir `raiz = pila_nodos[-1]` y devolver éxito con el árbol serializado (`raiz.a_dict()`).

Resultado: diccionario con `aceptada`, `error`, `pasos` (historial) y `arbol`.

---

## NodoParseo y serialización
- `NodoParseo(simbolo, hijos)` representa un nodo.
- `a_dict()` devuelve `{"simbolo": ..., "hijos": [...]}` recursivamente.
- La web recibe JSON y muestra el árbol.

---

## Consejos para la exposición (rápido)
- Muestra primero la gramática y cómo `leer_gramatica` la parsea (esto pone el contexto).
- Explica `FIRST` con un ejemplo pequeño y rápido (cómo itera hasta estabilizar).
- Para LR(1): dibuja un ítem y muestra `closure` agregando un `B -> · γ, b`.
- Enseña un estado `I0` y una transición `goto(I0, x) = I1`.
- Termina con el parseo real sobre la entrada de la demo (`x x y y`) y muestra la traza.

---

Si quieres, puedo:
- Añadir ejemplos concretos (por producción) mostrando cada paso de `closure` y `goto`.
- Generar diapositiva / fichas con los puntos clave.
- Empezar a repasar función por función en vivo: dime con cuál comenzamos y lo vemos línea a línea.
