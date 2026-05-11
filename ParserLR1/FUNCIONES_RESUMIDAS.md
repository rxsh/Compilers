# Guia de estudio del parser LR(1)

Este documento resume que hace cada parte de `parser.py` y como se conecta todo el algoritmo. La idea principal es:

1. Leer o inferir la gramatica.
2. Calcular `FIRST` y `FOLLOW`.
3. Aumentar la gramatica con `S' -> S`.
4. Construir los items LR(1), closures y transiciones.
5. Construir la tabla `ACTION/GOTO`.
6. Parsear la entrada usando pilas.
7. Devolver datos para la interfaz web.

---

## Constantes principales

### `EPSILON = "ε"`
Representa la cadena vacia. En el codigo, una produccion epsilon se guarda como lista vacia `[]`.

Ejemplo:

```txt
A -> ε
```

Se guarda como:

```python
("A", [])
```

### `EOF = "$"`
Representa el fin de la entrada. Siempre se agrega al final de los tokens que se van a parsear.

Ejemplo:

```python
["c", "d", "d"] -> ["c", "d", "d", "$"]
```

### `DOT = "·"`
Representa el punto de los items LR(1).

Ejemplo:

```txt
C -> · c C, d
C -> c · C, d
C -> c C ·, d
```

---

## Lectura e inferencia de gramatica

### `tokenizar_lista(texto)`

Convierte una linea de simbolos en una lista.

Ejemplo:

```txt
"c d"
```

Devuelve:

```python
["c", "d"]
```

Tambien tiene un caso especial para `"()"`, separandolo como `"("` y `")"`.

---

### `leer_gramatica(ruta)`

Lee una gramatica desde un archivo. Actualmente se usa para cargar `gramatica.txt`.

Internamente solo abre el archivo y manda el contenido a:

```python
leer_gramatica_desde_texto(...)
```

Esto permite reutilizar la misma logica para archivo y para texto escrito en la interfaz web.

---

### `leer_gramatica_desde_texto(texto)`

Es la funcion principal para interpretar la gramatica.

Acepta dos formatos.

Formato completo:

```txt
TERMINALES: c d
NO_TERMINALES: S C
INICIAL: S
PRODUCCIONES:
S -> C C
C -> c C
C -> d
```

Formato compacto:

```txt
S' -> S
S -> C C
C -> c C
C -> d
```

En el formato compacto, el parser infiere:

- Los no terminales salen de los lados izquierdos: `S`, `C`.
- Los terminales salen del lado derecho, excluyendo no terminales: `c`, `d`.
- Si la primera produccion es aumentada (`S' -> S`), la quita de las producciones reales y usa `S` como inicial.

Devuelve:

```python
terminales, no_terminales, inicial, producciones
```

Ejemplo:

```python
["c", "d"], ["S", "C"], "S", [
    ("S", ["C", "C"]),
    ("C", ["c", "C"]),
    ("C", ["d"]),
]
```

---

### `parsear_linea_produccion(linea, numero_linea)`

Convierte una linea como:

```txt
C -> c C | d
```

En varias producciones:

```python
("C", ["c", "C"])
("C", ["d"])
```

Tambien valida errores basicos:

- Si falta `->`.
- Si falta el lado izquierdo.

---

### `inferir_no_terminales(producciones)`

Obtiene los no terminales leyendo los lados izquierdos de las producciones.

Ejemplo:

```txt
S -> C C
C -> c C
C -> d
```

Devuelve:

```python
["S", "C"]
```

---

### `inferir_terminales(producciones, no_terminales)`

Obtiene los terminales leyendo los lados derechos de las producciones. Si un simbolo no esta en `no_terminales`, entonces se considera terminal.

Ejemplo:

```txt
S -> C C
C -> c C
C -> d
```

No terminales:

```python
["S", "C"]
```

Terminales inferidos:

```python
["c", "d"]
```

---

### `quitar_produccion_aumentada_si_existe(producciones, no_terminales)`

Detecta si la primera produccion ya viene aumentada.

Ejemplo:

```txt
S' -> S
S -> C C
```

Como `S'` termina en comilla y deriva a un no terminal, se interpreta como produccion aumentada visual. Entonces:

- El inicial real pasa a ser `S`.
- Se elimina `S' -> S` de las producciones reales.
- Luego el programa vuelve a crear la aumentada con `aumentar_gramatica`.

Esto evita duplicar:

```txt
S'' -> S'
S' -> S
```

---

## FIRST y FOLLOW

### `calcular_first(terminales, no_terminales, producciones)`

Calcula `FIRST(X)` para cada simbolo.

`FIRST(X)` significa: que terminales pueden aparecer al inicio de una cadena derivada desde `X`.

Inicializacion:

- Para cada terminal `t`: `FIRST(t) = {t}`.
- Para `$`: `FIRST($) = {$}`.
- Para `ε`: `FIRST(ε) = {ε}`.
- Para cada no terminal: empieza vacio.

Luego recorre las producciones muchas veces hasta que ya no haya cambios.

Ejemplo:

```txt
C -> c C
C -> d
```

Resultado:

```txt
FIRST(C) = {c, d}
```

Por que es importante: en LR(1), los lookaheads de nuevos items se calculan con `FIRST(βa)`.

---

### `calcular_follow(no_terminales, producciones, inicial, first)`

Calcula `FOLLOW(A)` para cada no terminal.

`FOLLOW(A)` significa: que simbolos pueden aparecer justo despues de `A` en alguna derivacion.

Regla inicial:

```txt
FOLLOW(inicial) contiene $
```

Ejemplo:

```txt
S -> C C
```

El primer `C` puede estar seguido por lo que empieza el segundo `C`, entonces puede tener `c` o `d` en su FOLLOW. El segundo `C` puede estar al final de `S`, entonces hereda `$`.

Nota: en el parser LR(1) la tabla usa principalmente los lookaheads de los items, pero `FOLLOW` se calcula y se muestra como dato de apoyo.

---

### `calcular_first_cadena(cadena, first)`

Calcula el FIRST de una secuencia completa, no solo de un simbolo.

Ejemplo:

```txt
FIRST(C $)
```

Si:

```txt
FIRST(C) = {c, d}
```

Entonces:

```txt
FIRST(C $) = {c, d}
```

Uso principal: en `closure`, para calcular los lookaheads nuevos.

---

## Gramatica aumentada y agrupacion

### `aumentar_gramatica(inicial, no_terminales, producciones)`

Agrega una nueva produccion inicial.

Si la gramatica original empieza en:

```txt
S
```

Se crea:

```txt
S' -> S
```

Esto es necesario para saber cuando aceptar la cadena. El parser acepta cuando llega al item:

```txt
S' -> S ·, $
```

Devuelve:

```python
inicial_aumentado, no_terminales_aumentados, producciones_aumentadas
```

---

### `agrupar_producciones(producciones)`

Convierte la lista de producciones en un diccionario por lado izquierdo.

Ejemplo:

```python
[
    ("C", ["c", "C"]),
    ("C", ["d"]),
]
```

Devuelve:

```python
{
    "C": [["c", "C"], ["d"]]
}
```

Sirve para que `closure` encuentre rapidamente todas las producciones de un no terminal.

---

## Formato de texto

### `formatear_produccion(lado_izq, lado_der)`

Convierte una produccion interna a texto.

Ejemplo:

```python
("C", ["c", "C"])
```

Devuelve:

```txt
C -> c C
```

Si el lado derecho es `[]`, devuelve:

```txt
C -> ε
```

---

### `formatear_lookaheads(lookaheads)`

Convierte un conjunto de anticipaciones a texto.

Ejemplo:

```python
["c", "d"]
```

Devuelve:

```txt
{c/d}
```

---

## Clases principales

### `ItemLR1`

Representa un item LR(1).

Tiene cuatro datos:

```python
lado_izq
lado_der
punto
anticipacion
```

Ejemplo conceptual:

```txt
C -> c · C, d
```

Se guarda como:

```python
ItemLR1("C", ("c", "C"), 1, "d")
```

Metodos importantes:

- `simbolo_despues_punto()`: devuelve el simbolo que esta justo despues del punto.
- `avanzar_punto()`: crea otro item con el punto una posicion mas a la derecha.
- `completado()`: indica si el punto ya llego al final.
- `texto()`: devuelve el item como texto.
- `nucleo()`: devuelve `(lado_izq, lado_der, punto)`, sin lookahead.
- `texto_sin_lookahead()`: muestra el item sin la anticipacion.

El nucleo sirve para agrupar items iguales que solo cambian en lookahead.

---

### `NodoParseo`

Representa un nodo del arbol de parseo.

Tiene:

```python
simbolo
hijos
```

Ejemplo:

```txt
S
├── C
└── C
```

El metodo `a_dict()` convierte el arbol a diccionario para mandarlo como JSON a la interfaz web.

---

## Closure, GOTO y estados LR(1)

### `closure(items, producciones_por_nt, no_terminales, first)`

Calcula la cerradura de un conjunto de items.

Idea:

Si un item tiene el punto antes de un no terminal:

```txt
A -> α · B β, a
```

Entonces se agregan las producciones de `B`:

```txt
B -> · γ, b
```

Donde:

```txt
b pertenece a FIRST(β a)
```

Ejemplo:

```txt
S -> · C C, $
```

El punto esta antes de `C`. Entonces se agregan:

```txt
C -> · c C, c
C -> · d, c
C -> · c C, d
C -> · d, d
```

Porque despues del primer `C` viene otro `C`, y:

```txt
FIRST(C $) = {c, d}
```

La funcion repite este proceso hasta que ya no se puedan agregar mas items.

---

### `ir_a(items, simbolo, producciones_por_nt, no_terminales, first)`

Implementa `GOTO(I, X)`.

Toma un estado `I` y un simbolo `X`.

Pasos:

1. Busca items donde el punto este antes de `X`.
2. Avanza el punto en esos items.
3. Calcula `closure` del resultado.

Ejemplo:

```txt
C -> · c C, d
```

Con `GOTO(I, c)` se convierte en:

```txt
C -> c · C, d
```

Y luego se calcula su closure.

---

### `coleccion_canonica_lr1(terminales, no_terminales, inicial, producciones, first)`

Construye todos los estados LR(1).

Pasos:

1. Crea el item inicial:

```txt
S' -> · S, $
```

2. Calcula su closure. Ese es el estado `I0`.
3. Para cada estado, prueba `GOTO` con cada terminal y no terminal.
4. Si aparece un estado nuevo, lo agrega a la lista.
5. Repite hasta que no queden estados pendientes.

Devuelve:

```python
estados, transiciones
```

Las transiciones tienen forma:

```python
(estado_origen, simbolo) -> estado_destino
```

---

## Tabla LR(1)

### `enumerar_producciones(producciones)`

Asigna numero a cada produccion.

Ejemplo:

```txt
(0) S' -> S
(1) S -> C C
(2) C -> c C
(3) C -> d
```

Es importante porque las reducciones se guardan como `r1`, `r2`, `r3`, etc.

---

### `construir_tabla_lr1(estados, transiciones, terminales, no_terminales, producciones, inicial_aumentado)`

Construye las tablas `ACTION` y `GOTO`.

`ACTION` se usa con terminales.

Puede tener:

- `shift`: mover un terminal y pasar a otro estado.
- `reduce`: reducir usando una produccion.
- `accept`: aceptar la cadena.

`GOTO` se usa con no terminales despues de una reduccion.

Reglas:

1. Si hay una transicion con terminal:

```txt
I --c--> J
```

Entonces:

```txt
ACTION[I, c] = shift J
```

2. Si hay una transicion con no terminal:

```txt
I --C--> J
```

Entonces:

```txt
GOTO[I, C] = J
```

3. Si hay un item completo:

```txt
A -> α ·, a
```

Entonces:

```txt
ACTION[I, a] = reduce A -> α
```

4. Si el item completo es el inicial aumentado:

```txt
S' -> S ·, $
```

Entonces:

```txt
ACTION[I, $] = accept
```

Tambien registra conflictos cuando una misma celda recibe dos acciones distintas.

---

## Parseo LR(1)

### `parsear_lr1(action, goto, producciones, tokens)`

Ejecuta el parser sobre una entrada.

Estructuras principales:

- `entrada`: tokens mas `$`.
- `pila_estados`: empieza con `[0]`.
- `pila_simbolos`: guarda terminales y no terminales reconocidos.
- `pila_nodos`: guarda nodos para construir el arbol.
- `historial`: guarda la traza para mostrarla en la web.

En cada paso:

1. Toma el estado en la cima de la pila.
2. Toma el token actual.
3. Busca:

```python
ACTION[estado, token_actual]
```

Casos:

### Shift

Si la accion es:

```txt
s4
```

Entonces:

- Mete el token en `pila_simbolos`.
- Mete el estado destino en `pila_estados`.
- Crea un nodo hoja para el token.
- Avanza al siguiente token de entrada.

### Reduce

Si la accion es:

```txt
r3
```

Entonces toma la produccion 3.

Ejemplo:

```txt
C -> d
```

Hace:

- Saca de la pila tantos simbolos como tenga el lado derecho.
- Crea un nodo `C` con esos hijos.
- Consulta `GOTO[estado_actual, C]`.
- Mete `C` y el nuevo estado a las pilas.

### Accept

Si la accion es:

```txt
acc
```

La cadena fue aceptada y se devuelve el arbol.

### Error

Si no existe accion para esa celda, la cadena se rechaza.

---

## Formateo de acciones

### `formatear_accion(accion, producciones)`

Convierte una accion interna a texto completo.

Ejemplo:

```python
("reduce", 3)
```

Puede mostrar:

```txt
reduce C -> d
```

---

### `formatear_accion_corta(accion)`

Convierte acciones al formato corto usado en la tabla y la traza.

Ejemplos:

```txt
("shift", 4)  -> s4
("reduce", 3) -> r3
("accept",)   -> acc
```

---

## Serializacion para la web

### `serializar_first(first)`

Convierte conjuntos de Python a listas ordenadas para poder enviarlos como JSON.

---

### `serializar_follow(follow)`

Hace lo mismo que `serializar_first`, pero con los conjuntos `FOLLOW`.

---

### `serializar_estados(estados, simbolo_inicial_aumentado=None)`

Convierte los estados LR(1) en texto legible para la interfaz.

Ademas agrupa items que tienen el mismo nucleo y diferentes lookaheads.

Ejemplo:

```txt
C -> · c C, c
C -> · c C, d
```

Se muestra como:

```txt
C -> · c C, {c/d}
```

Tambien separa:

- `items`: todos los items del closure.
- `kernel`: items principales del estado.

---

### `serializar_transiciones(transiciones)`

Convierte las transiciones internas:

```python
(0, "c") -> 1
```

En diccionarios JSON:

```python
{"desde": 0, "simbolo": "c", "hacia": 1}
```

---

### `serializar_tabla(action, goto, terminales, no_terminales, total_estados, producciones)`

Convierte `ACTION` y `GOTO` en filas para la tabla de la interfaz.

Ejemplo:

```python
{
    "estado": 0,
    "action": {"c": "s1", "d": "s2"},
    "goto": {"S": 3, "C": 4}
}
```

---

## Funciones de armado general

### `construir_demo_lr1(ruta_gramatica, tokens_entrada)`

Construye todo el resultado LR(1) leyendo la gramatica desde archivo.

Se usa para el demo inicial con `gramatica.txt`.

---

### `construir_demo_lr1_desde_texto(texto_gramatica, tokens_entrada)`

Construye todo el resultado LR(1) usando el texto escrito en la interfaz.

Esta es la funcion clave para la nueva version editable.

---

### `construir_demo_lr1_desde_componentes(...)`

Es la funcion central que une todo.

Recibe:

- Terminales.
- No terminales.
- Simbolo inicial.
- Producciones.
- Tokens de entrada.

Y ejecuta el flujo completo:

1. Calcula `FIRST`.
2. Calcula `FOLLOW`.
3. Aumenta la gramatica.
4. Recalcula `FIRST` con la gramatica aumentada.
5. Construye los estados LR(1).
6. Construye `ACTION/GOTO`.
7. Parsea la entrada.
8. Devuelve un diccionario con todo lo que usa la web.

---

### `formatear_gramatica_fuente(producciones_aumentadas, texto_fuente_original=None)`

Devuelve el texto que se mostrara en el editor de gramatica.

Si el usuario escribio una gramatica con secciones (`TERMINALES`, `NO_TERMINALES`, etc.), conserva ese texto.

Si uso formato compacto, muestra las producciones aumentadas:

```txt
S' -> S
S -> C C
C -> c C
C -> d
```

---

### `parsear_desde_gramatica(ruta_gramatica, tokens_entrada)`

Funcion auxiliar que devuelve solo:

- Entrada.
- Resultado del parseo.

Sirve si se quiere usar el parser sin toda la informacion visual.

---

### `imprimir_resumen_demo(datos)`

Imprime en consola:

- FIRST.
- Estados LR(1).
- Tabla LR(1).
- Pasos del parseo.
- Si la cadena fue aceptada.

Se usa cuando ejecutas:

```bash
python3 parser.py
```

---

## Flujo completo con ejemplo

Gramatica:

```txt
S' -> S
S -> C C
C -> c C
C -> d
```

Entrada:

```txt
c d d
```

El parser hace:

1. Detecta no terminales: `S`, `C`.
2. Detecta terminales: `c`, `d`.
3. Detecta inicial real: `S`.
4. Construye la aumentada: `S' -> S`.
5. Calcula `FIRST(S) = {c, d}` y `FIRST(C) = {c, d}`.
6. Crea el estado inicial con `S' -> · S, $`.
7. Aplica `closure` y agrega items de `S` y `C`.
8. Usa `GOTO` para construir todos los estados.
9. Llena `ACTION/GOTO`.
10. Procesa la entrada con shift y reduce.
11. Acepta cuando llega a `S' -> S ·, $`.

---

## Como explicar LR(1) en una frase

Un parser LR(1) lee la entrada de izquierda a derecha, construye una derivacion derecha en reversa, y usa un simbolo de anticipacion para decidir exactamente cuando hacer shift, reduce o accept.

---

## Preguntas que te pueden hacer

### 1. Por que se aumenta la gramatica con `S' -> S`?

Para tener una condicion clara de aceptacion. Cuando el parser llega a:

```txt
S' -> S ·, $
```

significa que ya reconocio todo el simbolo inicial y ademas la entrada termino.

---

### 2. Que significa el lookahead en un item LR(1)?

Es el terminal que puede venir despues de esa reduccion. Por ejemplo:

```txt
C -> d ·, c
```

significa que se puede reducir `C -> d` solamente si el siguiente token es `c`.

---

### 3. Cual es la diferencia entre `closure` y `goto`?

`closure` expande items cuando el punto esta antes de un no terminal.

`goto` mueve el punto sobre un simbolo y luego calcula el closure del resultado.

---

### 4. Que diferencia hay entre `ACTION` y `GOTO`?

`ACTION` se consulta con terminales y decide `shift`, `reduce`, `accept` o error.

`GOTO` se consulta con no terminales despues de una reduccion para saber a que estado saltar.

---

### 5. Por que LR(1) usa `FIRST(βa)` dentro de `closure`?

Porque cuando se agrega un item nuevo:

```txt
B -> · γ, b
```

el lookahead `b` depende de lo que puede aparecer despues de `B` en el item original:

```txt
A -> α · B β, a
```

Por eso se calcula:

```txt
FIRST(βa)
```

---

### 6. Cuando ocurre un reduce?

Ocurre cuando el punto esta al final de una produccion:

```txt
A -> α ·, a
```

Entonces, si el token actual es `a`, el parser reduce `α` a `A`.

---

### 7. Que pasa si una celda de `ACTION` recibe dos acciones?

Hay un conflicto. Puede ser:

- Shift/reduce.
- Reduce/reduce.

El codigo lo guarda en `conflictos` para mostrarlo en la interfaz.

---

### 8. Como sabe el parser si un simbolo es terminal o no terminal en el formato compacto?

Primero toma como no terminales todos los simbolos que aparecen a la izquierda de `->`.

Luego revisa los lados derechos. Si un simbolo aparece ahi y no esta en la lista de no terminales, entonces lo considera terminal.

---

### 9. Por que se usa una pila de estados y una pila de simbolos?

La pila de estados permite consultar la tabla LR(1). La pila de simbolos permite saber que parte de la entrada ya fue reconocida. En una reduccion, se sacan simbolos y estados, luego se mete el no terminal reducido y se consulta `GOTO`.

---

### 10. Para que sirve `pila_nodos`?

Sirve para construir el arbol de parseo al mismo tiempo que se hacen las reducciones. Cuando se reduce una produccion, los nodos del lado derecho se convierten en hijos del nuevo nodo del lado izquierdo.
