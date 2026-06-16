# Resumen del Scanner y Panic Mode

## Estado general

El scanner esta bien implementado y cumple la idea principal del proyecto:

- lee el texto fuente caracter por caracter
- genera tokens con tipo, lexema, linea y columna
- ignora espacios y comentarios
- reporta errores lexicos
- intenta recuperarse para seguir escaneando
- se integra con el parser LR(1)

Para presentacion y entrega academica esta bastante util.
El panic mode sigue siendo una recuperacion basica, pero ahora esta mejor resuelto en literales `STRING` mal formados.

---

## Estructura principal

### Archivo `scanner.py`

Contiene:

- `Token`
- `ScannerError`
- `Scanner`
- `escanear_fuente(...)`

### Flujo general

1. Se crea un `Scanner` con el texto fuente
2. El scanner usa `peekchar()` y `getchar()` para recorrer la entrada
3. `gettoken()` reconoce el siguiente token valido
4. `scan_all()` repite hasta llegar a `EOF`
5. El resultado se manda al parser a traves de `parser.py`

---

## Funciones importantes

### `peekchar()`

Devuelve el siguiente caracter sin consumirlo.

Sirve para mirar que viene antes de decidir que token leer.

### `getchar()`

Consume el siguiente caracter y actualiza:

- posicion
- linea
- columna

Es la base del scanner.

### `saltar_espacios_y_comentarios()`

Descarta:

- espacios
- tabulaciones
- saltos de linea
- comentarios con `#`

No genera tokens para ellos.

### `leer_identificador_o_keyword()`

Reconoce:

- identificadores `ID`
- palabras reservadas:
  - `bold`
  - `italic`
  - `color`
  - `upper`
  - `lower`

### `leer_numero()`

Reconoce numeros enteros y decimales simples.

### `leer_cadena()`

Reconoce strings entre comillas.

Soporta escapes:

- `\\`
- `\"`
- `\n`
- `\t`
- `\r`

Tambien detecta errores como:

- cadena sin cerrar
- escape invalido
- escape incompleto
- longitud maxima excedida

Si la cadena tiene un error serio, el scanner descarta el resto del literal hasta encontrar:

- comillas de cierre
- fin de linea
- fin de archivo

Eso evita que un `STRING` invalido siga circulando como si fuera correcto.

### `gettoken()`

Es la funcion principal del scanner.

Hace esto:

1. salta espacios y comentarios
2. revisa el siguiente caracter
3. decide si debe leer:
   - identificador
   - numero
   - cadena
   - token simple como `=`, `+`, `;`, `(`, `)`
4. si el simbolo no es valido, reporta error e intenta recuperarse

---

## Como esta hecho el panic mode

### Recuperacion en el scanner

La recuperacion principal esta en:

- `sincronizar_error()`
- `descartar_hasta_fin_de_literal()`
- la rama de error dentro de `gettoken()`

### Idea del algoritmo

Cuando encuentra algo invalido:

1. reporta el error
2. desecha la parte problematica
3. avanza hasta un punto razonable de reinicio
4. continua el escaneo

Eso incluye:

- espacio
- comentario
- letra
- digito
- comillas
- delimitadores simples

En strings mal formados:

- si hay escape invalido, se descarta el resto del literal
- si falta cerrar la cadena, se abandona el literal al llegar a salto de linea o EOF
- si supera el tamano maximo, tambien se descarta el resto del literal

### Eso si es panic mode?

Si, en una forma basica.

Porque el principio del panic mode es:

- abandonar la parte invalida
- avanzar hasta un punto razonable de reanudacion
- continuar el analisis

Y eso el scanner sí lo hace.

---

## Limitaciones importantes

### 1. Panic mode sigue siendo simple

El scanner no hace una recuperacion basada en contexto sintactico profundo.
Su estrategia es:

- abortar el token invalido
- saltar hasta un punto seguro
- reanudar

Eso esta bien para un proyecto academico, pero no es una recuperacion sofisticada como la de un compilador industrial.

### 2. Parser y scanner recuperan por separado

El scanner tiene recuperacion lexica.
El parser en `parser.py` ahora tiene recuperacion sintactica tipo panic mode basada en no terminales de recuperacion y tokens sincronizadores.

Eso esta bien conceptualmente, y conviene explicarlo como dos niveles distintos:

- recuperacion lexica
- recuperacion sintactica

### 3. Panic mode del parser LR(1)

Cuando ocurre un error sintactico, el parser hace esto:

1. detecta que `ACTION[estado, token]` no existe
2. registra el error
3. hace pop de la pila hasta encontrar un estado que tenga `goto` con algun no terminal de recuperacion
4. elige ese no terminal como punto de reinicio
5. descarta tokens de entrada hasta encontrar un token sincronizador
6. inserta un nodo artificial `"<error>"` dentro del arbol
7. continua el analisis desde ese punto

Los tokens sincronizadores se construyen con `FOLLOW(no_terminal) ∪ {$}`.

En esta gramatica, los no terminales de recuperacion priorizados son:

- `StmtList`
- `Stmt`
- `Expr`
- `ExprTail`
- `Term`
- `Factor`
- `FuncCall`
- `Literal`
- `Program`

Eso ya responde mejor a la idea clasica de panic mode que suelen pedir en clase para un parser LR(1).

---

## Conclusión honesta

### Lo que si puedes decir

- El scanner esta implementado correctamente como analizador lexico funcional
- Usa `getchar()`, `peekchar()` y `gettoken()`
- Produce tokens con ubicacion
- Maneja comentarios, espacios, strings, numeros, keywords e identificadores
- Tiene recuperacion de errores tipo panic mode basica
- Se integra con el parser LR(1)

### Lo que conviene matizar

- El scanner tiene panic mode lexico basico y funcional
- El parser tiene panic mode sintactico mas cercano al esquema academico LR
- En strings invalidos el token se descarta por completo
- La estrategia sigue siendo simple, pero ahora esta mejor alineada con la teoria

---

## Frase corta para presentar

Puedes decirlo asi:

> El sistema usa dos niveles de recuperacion. El scanner recupera errores lexicos descartando el token invalido hasta un punto seguro. El parser LR(1) recupera errores sintacticos cuando no existe `ACTION[estado, token]`: hace pop de pila hasta un estado util, elige un no terminal de recuperacion, descarta entrada hasta un token de `FOLLOW` y continua desde ahi.
