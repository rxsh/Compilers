# Explicacion del Proyecto LR(1)

Este documento explica que hace cada funcion, clase y modulo principal del proyecto. La idea es que te sirva para estudiar, exponer y entender como estan conectadas las partes.

---

## Vision general

El proyecto tiene dos partes:

1. `parser.py`
   Aqui vive toda la logica formal del parser LR(1):
   - lectura de la gramatica
   - calculo de `FIRST`
   - calculo de `FOLLOW`
   - construccion de items LR(1)
   - `closure`
   - `goto`
   - coleccion canonica
   - tabla `ACTION/GOTO`
   - parseo de una cadena
   - construccion del arbol de parseo

2. `server.py` y carpeta `web/`
   Esto conecta la logica anterior con una interfaz web:
   - `server.py` sirve la pagina
   - expone endpoints JSON
   - `web/app.js` consume esos datos
   - `web/index.html` y `web/styles.css` muestran la interfaz

---

## Constantes globales en `parser.py`

### `EPSILON = "ε"`
Representa la cadena vacia en la gramatica.

Se usa para:
- producciones vacias
- calculo de `FIRST`
- construccion del arbol cuando una reduccion corresponde a epsilon

### `EOF = "$"`
Representa el fin de la entrada.

Se usa para:
- lookahead final en LR(1)
- marcar el fin de los tokens
- detectar aceptacion

### `DOT = "·"`
Representa el punto dentro de un item LR(1).

Ejemplo:

```txt
E -> T · Ep, $
```

significa que ya se reconocio `T` y falta `Ep`.

---

## Funciones de lectura y preparacion de la gramatica

### `tokenizar_lista(texto)`

#### Para que sirve
Convierte una linea de terminales o no terminales en una lista de simbolos.

#### Entrada
Un texto como:

```txt
id + * ()
```

#### Salida
Una lista como:

```python
["id", "+", "*", "(", ")"]
```

#### Idea importante
Hace un caso especial para `"()"`, porque en el archivo de gramatica puede venir junto y aqui se separa en:

```python
"(" y ")"
```

---

### `leer_gramatica(ruta)`

#### Para que sirve
Lee el archivo `gramatica.txt` y devuelve la gramatica en estructuras que Python puede usar.

#### Devuelve
- `terminales`
- `no_terminales`
- `inicial`
- `producciones`

#### Como guarda las producciones
Cada produccion se guarda como:

```python
("E", ["T", "Ep"])
```

Si la produccion es epsilon:

```txt
Ep -> ε
```

internamente se guarda como:

```python
("Ep", [])
```

Eso es muy importante, porque asi `ε` no se trata como un token real dentro del parser.

#### Por que es util
Convierte el archivo de texto en una estructura formal que luego usan todas las demas funciones.

---

## FIRST y FOLLOW

### `calcular_first(terminales, no_terminales, producciones)`

#### Para que sirve
Calcula el conjunto `FIRST` de todos los simbolos de la gramatica.

#### Recordatorio teorico
`FIRST(X)` es el conjunto de simbolos terminales con los que puede empezar una derivacion de `X`.

Ejemplo:

```txt
F -> ( E ) | id
```

entonces:

```txt
FIRST(F) = { "(", "id" }
```

#### Como funciona
1. Inicializa:
   - `FIRST(terminal) = {terminal}`
   - `FIRST(ε) = {ε}`
   - `FIRST(no_terminal) = ∅`
2. Recorre las producciones muchas veces
3. Va agregando simbolos hasta que no cambie nada

#### Variable importante
`rhs`
Guarda temporalmente el `FIRST` de la parte derecha de una produccion.

#### Por que hace falta
Sin `FIRST` no puedes calcular lookaheads correctamente en LR(1).

---

### `calcular_follow(no_terminales, producciones, inicial, first)`

#### Para que sirve
Calcula el conjunto `FOLLOW` de cada no terminal.

#### Recordatorio teorico
`FOLLOW(A)` contiene los terminales que pueden aparecer inmediatamente despues de `A` en alguna derivacion.

#### Como funciona
1. Inicializa todos vacios
2. Al simbolo inicial le agrega `$`
3. Recorre producciones de derecha a izquierda
4. Usa la variable `trailer`

#### Variable importante
`trailer`
Representa lo que puede venir despues del simbolo actual mientras recorres una produccion desde la derecha.

#### Nota
En LR(1) puro no se necesita `FOLLOW` para construir la tabla, porque las reducciones usan lookaheads exactos. Igual sirve mucho para estudiar y para comparar con otros metodos como SLR.

---

### `calcular_first_cadena(cadena, first)`

#### Para que sirve
Calcula `FIRST` de una cadena de simbolos, no solo de un simbolo.

#### Ejemplo

```txt
FIRST(T Ep)
```

o dentro de LR(1):

```txt
FIRST(β a)
```

#### Por que es clave en LR(1)
En `closure`, cuando tienes un item como:

```txt
A -> α · B β, a
```

los nuevos lookaheads salen de:

```txt
FIRST(β a)
```

Sin esta funcion, no puedes construir bien los items LR(1).

---

## Preparacion de la gramatica para LR(1)

### `aumentar_gramatica(inicial, no_terminales, producciones)`

#### Para que sirve
Agrega una nueva produccion inicial:

```txt
S' -> S
```

#### Por que se hace
La gramatica aumentada permite detectar el estado de aceptacion.

#### Que devuelve
- `nuevo_inicial`
- `nuevos_no_terminales`
- `nuevas_producciones`

#### Idea central
El parser acepta cuando encuentra el item:

```txt
S' -> S ·, $
```

---

### `agrupar_producciones(producciones)`

#### Para que sirve
Agrupa las producciones por no terminal izquierdo.

#### Ejemplo
Si tienes:

```python
[
    ("F", ["(", "E", ")"]),
    ("F", ["id"])
]
```

lo deja como:

```python
{
    "F": [["(", "E", ")"], ["id"]]
}
```

#### Por que es util
En `closure`, cuando ves un no terminal despues del punto, necesitas encontrar rapidamente todas sus producciones.

---

### `formatear_produccion(lado_izq, lado_der)`

#### Para que sirve
Convierte una produccion en texto legible.

#### Ejemplos

```python
("F", ["id"]) -> "F -> id"
("Ep", []) -> "Ep -> ε"
```

#### Uso
Se usa para:
- mostrar producciones
- escribir reducciones
- serializar datos hacia la web

---

## Clase de item LR(1)

### `@dataclass(frozen=True) class ItemLR1`

#### Para que sirve
Representa formalmente un item LR(1).

#### Campos
- `lado_izq`: lado izquierdo de la produccion
- `lado_der`: lado derecho como tupla
- `punto`: posicion del punto
- `anticipacion`: lookahead

#### Ejemplo

```python
ItemLR1("E", ("T", "Ep"), 1, "$")
```

representa:

```txt
E -> T · Ep, $
```

#### Por que `frozen=True`
Hace que el objeto sea inmutable y hashable. Eso permite meterlo dentro de `set` y `frozenset`, que es justo lo que necesitamos para estados LR(1).

---

### `simbolo_despues_punto(self)`

#### Para que sirve
Devuelve el simbolo que esta inmediatamente despues del punto.

#### Ejemplo
Si el item es:

```txt
E -> T · Ep, $
```

devuelve:

```txt
Ep
```

Si el punto ya esta al final, devuelve `None`.

#### Uso
Se usa en `closure` y `goto`.

---

### `avanzar_punto(self)`

#### Para que sirve
Devuelve un nuevo item con el punto movido una posicion a la derecha.

#### Ejemplo

```txt
E -> · T Ep, $
```

pasa a:

```txt
E -> T · Ep, $
```

#### Uso
Se usa en `goto`.

---

### `completado(self)`

#### Para que sirve
Indica si el punto ya llego al final de la produccion.

#### Ejemplo

```txt
F -> id ·, +
```

ahi devuelve `True`.

#### Uso
Se usa para detectar reducciones y aceptacion al construir la tabla.

---

### `texto(self)` y `__str__(self)`

#### Para que sirven
Devuelven una version legible del item.

#### Ejemplo

```txt
E -> T · Ep, $
```

#### Uso
Se usa en impresiones por consola y en la serializacion para la web.

---

## Construccion de estados LR(1)

### `closure(items, producciones_por_nt, no_terminales, first)`

#### Para que sirve
Calcula la cerradura de un conjunto de items LR(1).

#### Regla teorica
Si tienes un item:

```txt
A -> α · B β, a
```

y `B` es no terminal, entonces debes agregar:

```txt
B -> · γ, b
```

para cada produccion `B -> γ` y para cada `b` en:

```txt
FIRST(β a)
```

#### Como funciona en el codigo
1. Parte con un conjunto inicial de items
2. Recorre cada item
3. Si el simbolo despues del punto es no terminal:
   - toma `beta`
   - le agrega la anticipacion actual
   - calcula `FIRST(beta + anticipacion)`
   - crea nuevos items con punto en 0
4. Repite hasta que no entren mas items nuevos

#### Por que es importante
`closure` es una de las funciones mas importantes de todo LR(1). Sin ella no puedes construir los estados correctamente.

---

### `ir_a(items, simbolo, producciones_por_nt, no_terminales, first)`

#### Para que sirve
Implementa `goto(I, X)`.

#### Idea teorica
Toma todos los items donde el punto esta antes de `X`, mueve el punto sobre `X` y luego aplica `closure`.

#### Como funciona
1. Busca items con `simbolo_despues_punto() == simbolo`
2. Avanza el punto
3. Si no hubo ninguno, devuelve vacio
4. Si hubo, calcula la cerradura de esos items movidos

#### Por que es importante
Con `goto` se generan las transiciones entre estados LR(1).

---

### `coleccion_canonica_lr1(terminales, no_terminales, inicial, producciones, first)`

#### Para que sirve
Construye toda la coleccion canonica de estados LR(1).

#### Que devuelve
- `estados`
- `transiciones`

#### Como funciona
1. Construye el item inicial:

```txt
S' -> · S, $
```

2. Le aplica `closure`
3. Ese resultado es el estado `I0`
4. Luego, para cada estado y cada simbolo, calcula `goto`
5. Si aparece un estado nuevo, lo agrega
6. Sigue hasta que ya no aparezcan mas estados

#### Por que es importante
La tabla LR(1) sale directamente de estos estados y sus transiciones.

---

## Producciones y tabla LR(1)

### `enumerar_producciones(producciones)`

#### Para que sirve
Asigna un indice a cada produccion.

#### Ejemplo

```python
0: S' -> S
1: S -> E
2: E -> T Ep
```

#### Uso
Sirve para referenciar reducciones por numero de produccion.

---

### `construir_tabla_lr1(estados, transiciones, terminales, no_terminales, producciones, inicial_aumentado)`

#### Para que sirve
Construye las tablas:
- `ACTION`
- `GOTO`

#### Como llena `ACTION`
1. Si desde un estado hay transicion con un terminal, pone `shift`
2. Si un item esta completado:
   - si es `S' -> S ·, $`, pone `accept`
   - si no, pone `reduce`

#### Como llena `GOTO`
Si la transicion es con un no terminal, se guarda en `goto`.

#### Variable importante
`conflictos`
Guarda conflictos si una misma casilla intenta recibir dos acciones distintas.

#### Por que es importante
La tabla es la estructura que usa el parser durante el reconocimiento de la cadena.

---

## Arbol de parseo

### `@dataclass class NodoParseo`

#### Para que sirve
Representa un nodo del arbol de parseo.

#### Campos
- `simbolo`
- `hijos`

#### Ejemplo

```python
NodoParseo("F", [NodoParseo("id", [])])
```

representa:

```txt
F
└── id
```

---

### `a_dict(self)`

#### Para que sirve
Convierte el nodo y sus hijos a diccionario.

#### Por que hace falta
La web no puede usar directamente objetos Python, pero si puede recibir JSON.

Entonces:

```python
NodoParseo(...)
```

se transforma en:

```python
{
  "simbolo": "...",
  "hijos": [...]
}
```

---

## Parseo LR(1)

### `parsear_lr1(action, goto, producciones, tokens)`

#### Para que sirve
Ejecuta el parser LR(1) sobre una lista de tokens.

#### Que usa
- tabla `ACTION`
- tabla `GOTO`
- producciones
- tokens de entrada

#### Pilas que maneja
1. `pila_estados`
   Guarda los estados del automata LR

2. `pila_simbolos`
   Guarda los simbolos reconocidos

3. `pila_nodos`
   Guarda nodos del arbol de parseo

#### Flujo general
1. Mira el estado de arriba
2. Mira el token actual
3. Busca `ACTION[estado, token]`
4. Si la accion es:
   - `shift`: mete el token y el nuevo estado
   - `reduce`: saca elementos de la pila y crea un nodo
   - `accept`: termina con exito
   - `None`: error

#### Variable importante
`historial`
Guarda cada paso del parseo para que luego la web pueda mostrar la traza.

#### Caso de reduccion
Si la produccion es:

```txt
F -> id
```

el parser:
- saca `id`
- crea nodo `F`
- mete `F`
- consulta `goto`

#### Caso epsilon
Si la produccion es vacia, crea un nodo hijo `ε`.

#### Resultado final
Devuelve un diccionario con:
- si la cadena fue aceptada
- error si existe
- pasos de la traza
- arbol de parseo

---

### `formatear_accion(accion, producciones)`

#### Para que sirve
Convierte una accion interna en texto legible.

#### Ejemplos

```txt
("shift", 5) -> "shift 5"
("reduce", 3) -> "reduce Ep -> + T Ep"
("accept",) -> "accept"
```

#### Uso
Se usa para:
- la traza
- la tabla serializada
- mensajes en la interfaz

---

## Serializacion de datos para la web

### `serializar_first(first)`
Convierte los conjuntos `FIRST` a listas ordenadas para poder enviarlos como JSON.

### `serializar_follow(follow)`
Hace lo mismo con `FOLLOW`.

### `serializar_estados(estados)`
Convierte los estados LR(1) a una lista de diccionarios legibles por la web.

### `serializar_transiciones(transiciones)`
Convierte el mapa de transiciones a una lista con:
- estado origen
- simbolo
- estado destino

### `serializar_tabla(action, goto, terminales, no_terminales, total_estados, producciones)`

#### Para que sirve
Convierte la tabla LR(1) a una estructura facil de renderizar en HTML.

#### Salida
Una lista de filas, donde cada fila tiene:
- `estado`
- `action`
- `goto`

---

## Orquestacion general

### `construir_demo_lr1(ruta_gramatica, tokens_entrada)`

#### Para que sirve
Es la funcion principal que arma toda la informacion del sistema.

#### Que hace en orden
1. Lee la gramatica
2. Calcula `FIRST`
3. Calcula `FOLLOW`
4. Aumenta la gramatica
5. Construye estados LR(1)
6. Construye tabla LR(1)
7. Ejecuta el parseo con los tokens
8. Serializa todo para la web

#### Por que es tan importante
Es la funcion central que conecta toda la teoria:
- gramatica
- conjuntos
- estados
- tabla
- parseo
- arbol

La interfaz web consume practicamente el resultado de esta funcion.

---

### `parsear_desde_gramatica(ruta_gramatica, tokens_entrada)`

#### Para que sirve
Es una funcion auxiliar.

#### Que hace
Llama a `construir_demo_lr1(...)` y devuelve solo:
- la entrada
- el resultado del parseo

#### Nota
Sirve si en algun momento quieres separar la carga de la gramatica del parseo puntual.

---

### `imprimir_resumen_demo(datos)`

#### Para que sirve
Imprime por consola un resumen de:
- `FIRST`
- estados LR(1)
- tabla
- pasos del parseo

#### Uso
Es util para depurar sin abrir la interfaz web.

---

## `server.py`

### Idea general
Este archivo levanta un servidor HTTP local sin depender de frameworks externos.

---

### `BASE_DIR`, `WEB_DIR`, `GRAMMAR_FILE`

#### Para que sirven
Guardan rutas importantes:
- carpeta base del proyecto
- carpeta web
- archivo de gramatica

---

### `class LR1RequestHandler(BaseHTTPRequestHandler)`

#### Para que sirve
Maneja las peticiones HTTP.

---

### `do_GET(self)`

#### Para que sirve
Atiende peticiones GET.

#### Rutas
- `/api/demo`
  devuelve toda la informacion inicial
- cualquier otra ruta
  intenta servir archivos estaticos de la carpeta `web`

---

### `do_POST(self)`

#### Para que sirve
Atiende peticiones POST.

#### Ruta principal
- `/api/parse`
  recibe tokens y devuelve el parseo real

---

### `handle_demo(self)`

#### Para que sirve
Construye una demo completa usando la gramatica real y una cadena inicial.

#### Uso
La web la llama al cargarse por primera vez.

---

### `handle_parse(self)`

#### Para que sirve
Lee el JSON enviado por la web, extrae los tokens y ejecuta el parser real.

#### Respuesta
Devuelve el mismo tipo de estructura que usa la interfaz.

---

### `handle_static(self, path)`

#### Para que sirve
Sirve archivos como:
- `index.html`
- `styles.css`
- `app.js`

#### Medida de seguridad
Valida que la ruta resuelta quede dentro de la carpeta `web`.

---

### `send_json(self, data, status=200)`

#### Para que sirve
Envuelve la respuesta JSON:
- serializa
- pone headers
- envia el contenido

---

### `run_server(host="127.0.0.1", port=8000)`

#### Para que sirve
Inicia el servidor HTTP.

#### Ejecucion

```powershell
py server.py
```

o

```powershell
python server.py
```

Luego se abre:

```txt
http://127.0.0.1:8000
```

---

## Parte web

## `web/index.html`

Define la estructura visual:
- panel de gramatica
- closure table
- tabla FIRST
- LR table
- input de tokens
- trace
- tree

---

## `web/styles.css`

Define la apariencia:
- layout
- paneles
- tablas
- colores
- arbol

---

## `web/app.js`

### Responsabilidad general
Conectar la interfaz HTML con el backend Python.

### Flujo principal
1. Al abrir la pagina hace `fetch("/api/demo")`
2. Renderiza todos los paneles
3. Al pulsar `Parse`, envia los tokens a `fetch("/api/parse")`
4. Recibe el parseo real
5. Actualiza traza y arbol

### Funciones visuales importantes
- `renderData(...)`
- `renderGrammar(...)`
- `renderFirstTable(...)`
- `renderClosureTable(...)`
- `renderLRTable(...)`
- `renderTrace(...)`
- `renderTree(...)`
- `renderConflicts(...)`

Cada una toma una parte del JSON y la convierte en HTML visible.

---

## Como lo explicarias en una exposicion

Una forma clara de explicarlo seria:

1. Leo la gramatica desde un archivo de texto
2. Calculo `FIRST` y `FOLLOW`
3. Aumento la gramatica con `S' -> S`
4. Construyo items LR(1)
5. A partir de ellos calculo `closure` y `goto`
6. Con eso genero la coleccion canonica de estados
7. Desde los estados construyo la tabla `ACTION/GOTO`
8. El parser usa esa tabla para decidir `shift`, `reduce` o `accept`
9. Mientras parsea, construye tambien el arbol
10. Finalmente, muestro todo en una interfaz web

---

## Que deberias aprenderte bien

Si quieres dominar este proyecto, yo me enfocaria en entender muy bien estas piezas:

1. Que es un item LR(1)
2. Que hace `closure`
3. Que hace `goto`
4. Como se forma la tabla `ACTION/GOTO`
5. Como trabaja la pila del parser
6. Como una reduccion se convierte en un nodo del arbol

Si esas seis cosas las entiendes, ya entiendes el corazon del proyecto.

---

## Idea final

No intentes memorizar cada linea exacta del codigo. Es mejor memorizar:
- la idea de cada funcion
- que entra
- que sale
- por que hace falta
- como se conecta con la siguiente

Si entiendes esa cadena, ya no estas repitiendo codigo: lo estas comprendiendo.
