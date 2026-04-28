# FUNCIONES RESUMIDAS — LR(1) (para presentar)

Versión breve y clara de las funciones que debes explicar en la exposición.

---

## tokenizar_lista(texto)
- Propósito: convertir una línea de símbolos en una lista Python.
- Cómo: `texto.split()` y caso especial para `"()"` → `"("`, `")"`.
- Uso: leer las secciones `TERMINALES` y `NO_TERMINALES`.

---

## leer_gramatica(ruta)
- Propósito: parsear `gramatica.txt` y devolver `(terminales, no_terminales, inicial, producciones)`.
- Cómo: detecta secciones por prefijos; en `PRODUCCIONES` separa alternativas `A -> a | b` en tuplas `(A, [simbolos])`.
- Nota: producción con ε se guarda como `("A", [])`.

---

## calcular_first(terminales, no_terminales, producciones)
- Propósito: calcular `FIRST(symbol)` para todos los símbolos.
- Cómo (resumen): inicializa `FIRST(terminal)={terminal}`, `FIRST(ε)={ε}`, `FIRST(no_terminal)=∅`; itera sobre producciones acumulando FIRST(RHS) hasta convergencia.
- Importancia: necesario para los lookaheads de LR(1).

---

## calcular_first_cadena(cadena, first)
- Propósito: `FIRST` de una secuencia (ej. `β a`).
- Cómo: recorre símbolos a la izquierda, agrega `FIRST(simbolo) - {ε}`; si todos producen ε, agrega ε.
- Uso: en `closure` para calcular `FIRST(β a)`.

---

## closure(items, producciones_por_nt, no_terminales, first)
- Propósito: expandir un conjunto de items LR(1) según la definición de cerradura.
- Cómo (resumen): para cada item con `·` antes de un no-terminal B, calcula `FIRST(β a)` (β = resto, a = lookahead) y agrega `B -> · γ, b` para cada producción `γ` de B y cada `b` en ese FIRST; repetir hasta estabilidad.
- Punto clave: LR(1) usa `FIRST(β a)` para propagar lookaheads correctamente.

---

## ir_a(items, simbolo, producciones_por_nt, no_terminales, first)
- Propósito: `goto(I, X)`.
- Cómo: avanza el punto en items con `·` antes de `X`, y aplica `closure` al resultado.

---

## coleccion_canonica_lr1(terminales, no_terminales, inicial, producciones, first)
- Propósito: construir todos los estados LR(1) (cerraduras) y transiciones.
- Cómo: `I0 = closure({S' -> · S, $})`; para cada estado y cada símbolo calcula `goto`; si aparece un estado nuevo, lo añade; repetir hasta agotar.
- Resultado: lista de estados y mapa de transiciones.

---

## construir_tabla_lr1(estados, transiciones, terminales, no_terminales, producciones, inicial_aumentado)
- Propósito: construir `ACTION` y `GOTO`.
- Cómo:
  - De las transiciones: terminal → `shift`, no-terminal → `goto`.
  - De items completados: `S' -> S ·, $` → `accept`; `A -> α ·, a` → `reduce` en `(estado, a)`.
- Manejo de conflictos: registra shift/reduce o reduce/reduce en `conflictos`.

---

## parsear_lr1(action, goto, producciones, tokens)
- Propósito: reconocer la entrada con la tabla LR(1), construir traza y árbol.
- Estructuras:
  - `entrada = tokens + [$]`
  - `pila_estados` (inicia `[0]`), `pila_simbolos`, `pila_nodos` (para construir el árbol), `historial` (traza)
- Flujo (resumen): en cada paso lee `ACTION[estado, token]`:
  - `shift`: push token, push estado destino, crear nodo hoja; avanzar entrada.
  - `reduce`: pop |α| elementos, crear `NodoParseo(A, hijos)`, consultar `GOTO` y push A y estado destino.
  - `accept`: éxito; `None` → error.
- `historial` contiene las copias de `pila_estados`, `pila_simbolos`, `entrada` y la `accion` corta (`sX`/`rY`/`acc`) en cada paso — eso se muestra en la web.

---

## NodoParseo (árbol)
- `NodoParseo(simbolo, hijos)`: nodo del árbol de parseo.
- `a_dict()`: convierte recursivamente a diccionario JSON para la interfaz.
- En `reduce`, los hijos se obtienen pop-eando nodos de la pila y revirtiéndolos para mantener orden.

---

## Serialización para la web
- `serializar_first` / `serializar_follow`: conjuntos → listas ordenadas para JSON.
- `serializar_estados`: agrupa items por núcleo (ignora lookahead al agrupar), junta lookaheads y produce `items` y `kernel` legibles.

---

## Seguimiento (trace) — qué mostrar y por qué
- Cada paso guarda: `pila_estados`, `pila_simbolos`, `entrada` y la `accion`.
- Esto permite explicar en la exposición por qué el parser decide `shift` o `reduce` y cómo evoluciona la pila y el árbol.

---

Si quieres, lo puedo convertir en fichas para diapositivas o recortarlo aún más por sección.
