# Guía de Funciones del Proyecto LR(1)

Este documento resume las funciones y bloques más importantes del proyecto, con foco en:

- scanner
- recuperación de errores
- parser LR(1)
- acciones ad hoc
- traducción del documento

La idea es que te sirva para estudiar y explicarlo en una revisión.

---

## 1. Visión general

El proyecto está dividido en dos partes principales:

1. `scanner.py`
   Se encarga del análisis léxico.
   Lee caracteres y los convierte en tokens.

2. `parser.py`
   Se encarga del análisis sintáctico LR(1), la recuperación de errores del parser, la construcción del árbol y la traducción final del documento.

El flujo general es este:

1. El scanner lee el texto fuente.
2. Produce tokens con tipo, lexema, línea y columna.
3. El parser LR(1) recibe esos tokens.
4. El parser usa la tabla LR(1) para decidir `shift`, `reduce`, `accept` o `error`.
5. Mientras reduce, ejecuta acciones ad hoc.
6. Al final construye el árbol y también el documento traducido.

---

## 2. Scanner (`scanner.py`)

## Objetivo

Convertir el texto fuente en una secuencia de tokens que el parser pueda entender.

## Estructuras principales

### `Token`

Representa un token válido.

Campos:

- `tipo`: categoría del token
- `lexema`: texto exacto leído
- `linea`: línea donde empieza
- `columna`: columna donde empieza

### `ScannerError`

Representa un error léxico.

Campos:

- `mensaje`
- `linea`
- `columna`

### `Scanner`

Es la clase principal del análisis léxico.

Guarda:

- el texto fuente
- posición actual
- línea y columna actuales
- lista de errores
- traza de depuración

---

## Funciones importantes del scanner

### `peekchar()`

Mira el siguiente carácter sin avanzar.

Sirve para decidir qué tipo de token empieza en la posición actual.

### `getchar()`

Consume el siguiente carácter y avanza el puntero.

También actualiza:

- `self.pos`
- `self.linea`
- `self.columna`

Si el carácter es `\n`, incrementa la línea y reinicia la columna.

### `agregar_traza(evento, detalle, linea=None, columna=None)`

Guarda eventos de depuración del scanner.

Esto permite mostrar en la web cómo fue leyendo tokens y errores.

### `reportar_error(mensaje, linea, columna)`

Registra un error léxico y además lo agrega a la traza.

### `descartar_hasta_fin_de_literal()`

Se usa cuando una cadena está mal formada.

La idea es descartar el resto del literal hasta encontrar:

- comilla de cierre
- salto de línea
- EOF

Esto evita que el scanner siga interpretando basura como si fuera parte de la cadena.

### `saltar_espacios_y_comentarios()`

Descarta:

- espacios
- tabs
- saltos de línea
- comentarios que empiezan con `#`

Estos no se devuelven como tokens.

### `leer_identificador_o_keyword()`

Lee secuencias como:

- `titulo`
- `section`
- `paragraph`
- `bold`

Si el lexema está en `KEYWORDS`, el tipo del token será esa palabra reservada.
Si no, será `ID`.

### `leer_numero()`

Reconoce literales numéricos simples.

### `leer_cadena()`

Lee cadenas entre comillas.

También valida:

- cadena sin cerrar
- escape inválido
- escape incompleto
- tamaño máximo del literal

Esta es una de las funciones más importantes del scanner porque concentra buena parte del manejo de errores léxicos.

### `sincronizar_error()`

Es la función de recuperación de errores del scanner.

Cuando aparece un símbolo inválido, avanza hasta un punto razonable donde pueda empezar otro token válido.

Por ejemplo, puede detenerse si encuentra:

- espacio
- delimitador
- letra
- dígito
- comillas

### `gettoken()`

Es la función principal del scanner.

Hace esto:

1. llama a `saltar_espacios_y_comentarios()`
2. revisa el siguiente carácter
3. decide si debe leer:
   - identificador o keyword
   - número
   - cadena
   - token simple
4. si encuentra error, lo reporta y trata de recuperarse

Esta es la función que conceptualmente invoca el parser.

### `scan_all()`

Llama repetidamente a `gettoken()` hasta producir `EOF`.

### `escanear_fuente(fuente, max_literal_length=1024)`

Es un envoltorio práctico.

Construye un `Scanner`, ejecuta el escaneo completo y devuelve:

- tokens
- errores
- traza

---

## 3. Recuperación de errores en el scanner

La recuperación léxica es tipo panic mode básico.

## Idea

Cuando el scanner encuentra algo inválido:

1. informa el error
2. descarta el fragmento problemático
3. busca un punto seguro
4. continúa escaneando

## Funciones que participan

- `reportar_error()`
- `descartar_hasta_fin_de_literal()`
- `sincronizar_error()`
- `gettoken()`

## Casos importantes que maneja

- símbolo no reconocido
- cadena sin cerrar
- escape inválido
- escape incompleto
- cadena demasiado larga

## Cómo explicarlo en clase

Puedes decirlo así:

> El scanner implementa una recuperación de errores léxicos tipo panic mode. Cuando encuentra una secuencia inválida, reporta el error, descarta la parte problemática y avanza hasta un punto donde razonablemente pueda empezar otro token válido.

---

## 4. Base de la gramática y conjuntos FIRST/FOLLOW (`parser.py`)

Estas funciones preparan la gramática para construir el parser.

### `leer_gramatica(ruta)`

Lee el archivo de gramática desde disco.

### `leer_gramatica_desde_texto(texto)`

Lee la gramática desde un string.

Se usa cuando la gramática se edita desde la web.

### `parsear_linea_produccion(linea, numero_linea)`

Convierte una línea como:

```txt
ExprTail -> + Term ExprTail | ε
```

en producciones internas.

### `inferir_no_terminales(...)`

Infere no terminales a partir de los lados izquierdos.

### `inferir_terminales(...)`

Infere terminales viendo qué símbolos no son no terminales.

### `quitar_produccion_aumentada_si_existe(...)`

Si la gramática ya trae una producción aumentada visible, la separa.

### `calcular_first(...)`

Calcula `FIRST` de:

- terminales
- no terminales
- `ε`
- `$`

### `calcular_follow(...)`

Calcula `FOLLOW` para cada no terminal.

Es importante porque luego se usa para sincronización del panic mode del parser.

### `calcular_first_cadena(cadena, first)`

Calcula `FIRST` no de un símbolo, sino de una cadena completa de símbolos.

Esto es clave en LR(1) para calcular anticipaciones.

### `aumentar_gramatica(...)`

Crea la gramática aumentada agregando el nuevo símbolo inicial.

---

## 5. Estructuras internas del parser

### `ItemLR1`

Representa un ítem LR(1).

Contiene:

- lado izquierdo
- lado derecho
- posición del punto
- lookahead

Métodos importantes:

- `simbolo_despues_punto()`
- `avanzar_punto()`
- `completado()`
- `nucleo()`

### `NodoParseo`

Representa un nodo del árbol de parseo.

Cada nodo tiene:

- `simbolo`
- `hijos`

Y se puede serializar con `a_dict()`.

---

## 6. Construcción LR(1)

### `closure(items, producciones_por_nt, no_terminales, first)`

Calcula la cerradura de un conjunto de ítems LR(1).

Si el punto está antes de un no terminal, agrega las producciones correspondientes con sus lookaheads.

### `ir_a(items, simbolo, producciones_por_nt, no_terminales, first)`

Implementa `goto`.

Mueve el punto sobre un símbolo y luego aplica `closure`.

### `coleccion_canonica_lr1(...)`

Construye la colección canónica de estados LR(1).

Devuelve:

- lista de estados
- transiciones entre estados

### `construir_tabla_lr1(...)`

Construye:

- `ACTION`
- `GOTO`

También detecta conflictos.

### `enumerar_producciones(...)`

Numera producciones para mostrar `r1`, `r2`, etc.

---

## 7. Recuperación de errores en el parser LR(1)

Esta es la parte más importante para tu exposición.

## Idea general

Cuando el parser busca `ACTION[estado, token]` y no encuentra nada:

1. detecta el error sintáctico
2. registra el error
3. hace pop de la pila hasta encontrar un estado útil
4. busca un no terminal de recuperación
5. descarta tokens de entrada hasta llegar a un token sincronizador
6. continúa el parseo

Eso es panic mode sintáctico.

## Funciones importantes

### `ordenar_no_terminales_recuperacion(no_terminales)`

Define un orden de prioridad para intentar recuperarse.

Por ejemplo, intenta primero con símbolos altos de la estructura como:

- `StmtList`
- `Stmt`
- `DocStmt`
- `Expr`

La idea es recuperar en un punto sintáctico razonable.

### `recuperar_en_parser_lr1(...)`

Esta es la función central del panic mode del parser.

Hace esto:

1. toma el estado actual del tope de pila
2. prueba si existe `goto[estado, NT]` para algún no terminal de recuperación
3. si existe:
   - descarta tokens hasta encontrar un sincronizador
   - inserta un nodo artificial de error
   - empuja el no terminal recuperado
   - continúa
4. si no encuentra nada, sigue haciendo pop

Los sincronizadores se construyen con:

```txt
FOLLOW(NT) ∪ {$}
```

### `parsear_lr1(...)`

Es el corazón del parser.

Hace el ciclo principal:

- lee el estado actual
- mira el token actual
- consulta `ACTION`
- ejecuta `shift`
- ejecuta `reduce`
- acepta
- o recupera error

## Qué pilas maneja

`parsear_lr1()` maneja varias pilas al mismo tiempo:

- `pila_estados`
- `pila_simbolos`
- `pila_nodos`
- `pila_semantica`

Eso permite que el parser:

- haga análisis sintáctico
- construya árbol
- ejecute acciones semánticas
- traduzca al mismo tiempo

## Cómo explicarlo en clase

Puedes decirlo así:

> Cuando no existe `ACTION[estado, token]`, el parser entra en panic mode. Hace pop de la pila hasta encontrar un estado desde el cual pueda reinsertar un no terminal de recuperación usando `goto`. Luego descarta entrada hasta un token sincronizador derivado de `FOLLOW`, inserta un marcador de error y continúa.

---

## 8. Acciones ad hoc y traducción

Aquí está la parte semántica del proyecto.

La idea es: no solo parsear, sino traducir el documento mientras se reduce.

## Funciones auxiliares semánticas

### `escape_html(texto)`

Escapa caracteres HTML especiales.

### `crear_valor(...)`

Crea una estructura semántica uniforme con:

- `texto`
- `html`
- `tipo`

Esto ayuda a que todas las reducciones produzcan un resultado compatible.

### `crear_token_semantico(token)`

Convierte un token escaneado en una forma útil para la pila semántica.

### `desescapar_literal_string(lexema)`

Convierte el lexema de una cadena a su contenido real.

Ejemplo:

```txt
"hola\n"
```

se transforma al texto interno correspondiente.

### `sanitizar_color_css(texto)`

Traduce nombres de colores a valores CSS seguros.

Ejemplos:

- `verde` -> `green`
- `rojo` -> `red`

### `aplicar_funcion_documento(nombre, argumento)`

Aplica funciones de formato de un argumento:

- `bold(...)`
- `italic(...)`
- `upper(...)`
- `lower(...)`

### `aplicar_color_documento(color_valor, contenido_valor)`

Aplica color a un contenido.

Ejemplo:

```txt
color("verde", "texto")
```

produce un `span` con `style="color: green"`.

### `crear_contexto_traduccion()`

Crea el contexto semántico.

Hoy guarda:

- variables
- advertencias

### `clonar_valor_semantico(valor)`

Evita compartir referencias peligrosas cuando se reutilizan valores.

### `resolver_identificador(nombre, contexto)`

Busca una variable previamente asignada.

Si no existe:

- agrega advertencia
- devuelve un valor especial visualizando que quedó sin resolver

### `construir_documento_traducido(programa, contexto)`

Toma el resultado semántico final y construye el documento HTML final.

Esa es la salida traducida que luego se muestra en la web y se exporta a PDF mediante impresión del navegador.

---

## 9. La función más importante de traducción: `aplicar_accion_semantica(...)`

Esta función implementa las acciones ad hoc de cada producción.

Se ejecuta cada vez que el parser hace una reducción.

## Qué hace

Dependiendo de qué producción se reduzca:

- construye la estructura del programa
- concatena expresiones
- resuelve identificadores
- guarda variables
- crea secciones
- crea párrafos
- crea listas
- aplica formatos

## Ejemplos de acciones

### Asignación

```txt
Stmt -> ID = Expr
```

Guarda el valor de `Expr` dentro de `contexto["variables"]`.

### Sección

```txt
DocStmt -> section ( Expr )
```

Convierte la expresión en:

```html
<h1 class='doc-section'>...</h1>
```

### Párrafo

```txt
DocStmt -> paragraph ( Expr )
```

Convierte la expresión en:

```html
<p class='doc-paragraph'>...</p>
```

### Lista

```txt
DocStmt -> itemize ( ItemList )
```

Genera un bloque:

```html
<ul class='doc-list'>...</ul>
```

### Color

```txt
FuncCall -> color ( Expr , Expr )
```

El primer `Expr` indica el color.
El segundo `Expr` indica el contenido.

---

## 10. Funciones de serialización y demo

Estas funciones preparan los datos para la web.

### `serializar_first(...)`

Convierte `FIRST` a formato JSON amigable.

### `serializar_follow(...)`

Convierte `FOLLOW` a formato JSON amigable.

### `serializar_estados(...)`

Convierte los estados LR(1) a una estructura visualizable.

### `serializar_transiciones(...)`

Convierte las transiciones `goto` en datos para la tabla.

### `serializar_tabla(...)`

Convierte `ACTION/GOTO` en filas aptas para la UI.

### `construir_demo_lr1_desde_componentes(...)`

Es la función integradora principal.

Hace todo:

1. calcula `FIRST`
2. calcula `FOLLOW`
3. aumenta gramática
4. construye estados LR(1)
5. construye tabla LR(1)
6. define recuperación por panic mode
7. llama al parser
8. empaqueta todo para la web

### `construir_demo_lr1_desde_componentes_con_scanner(...)`

Primero llama al scanner y luego al parser.

Esta es la ruta más completa del sistema.

---

## 11. Qué funciones deberías conocer sí o sí

Si te preguntan en revisión, prioriza estas:

### Del scanner

- `peekchar()`
- `getchar()`
- `leer_cadena()`
- `sincronizar_error()`
- `gettoken()`

### Del parser LR(1)

- `calcular_first()`
- `calcular_first_cadena()`
- `closure()`
- `ir_a()`
- `construir_tabla_lr1()`
- `parsear_lr1()`

### De recuperación de errores

- `sincronizar_error()` en el scanner
- `ordenar_no_terminales_recuperacion()`
- `recuperar_en_parser_lr1()`

### De acciones ad hoc y traducción

- `aplicar_accion_semantica()`
- `aplicar_funcion_documento()`
- `aplicar_color_documento()`
- `resolver_identificador()`
- `construir_documento_traducido()`

---

## 12. Resumen oral corto para presentar

Puedes decirlo así:

> El scanner transforma el texto fuente en tokens usando `peekchar`, `getchar` y `gettoken`, y además implementa recuperación léxica básica tipo panic mode.  
> El parser construye la tabla LR(1) a partir de `FIRST`, `closure` y `goto`, y luego parsea usando `ACTION/GOTO`.  
> Si encuentra un error sintáctico, entra en panic mode: hace pop de la pila, busca un no terminal de recuperación, sincroniza con `FOLLOW` y continúa.  
> Durante las reducciones, el parser ejecuta acciones ad hoc en `aplicar_accion_semantica`, lo que permite traducir el documento al mismo tiempo que se analiza.  
> Al final, el sistema produce el árbol de parseo, la traza del parser, la salida del scanner y el documento traducido.

