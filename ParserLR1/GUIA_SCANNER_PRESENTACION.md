# Guia Rapida del Scanner

Este documento resume como funciona el scanner del proyecto y como explicar su recuperacion de errores en la presentacion.

---

## 1. Que hace el scanner

El scanner toma el texto fuente y lo convierte en tokens.

Cada token lleva:

- tipo
- lexema
- linea
- columna

Despues, esos tokens se envian al parser LR(1).

---

## 2. Estructuras principales

### `Token`

Representa un token valido.

Campos:

- `tipo`
- `lexema`
- `linea`
- `columna`

### `ScannerError`

Representa un error lexico.

Campos:

- `mensaje`
- `linea`
- `columna`

### `Scanner`

Es la clase que recorre el texto fuente y reconoce tokens.

Guarda:

- la fuente original
- la posicion actual
- la linea actual
- la columna actual
- la lista de errores
- la traza de depuracion

---

## 3. Funciones del scanner

### `peekchar()`

Mira el siguiente caracter sin consumirlo.

Se usa para decidir que token empieza.

### `getchar()`

Consume el siguiente caracter y avanza la posicion.

Tambien actualiza:

- linea
- columna

### `agregar_traza(evento, detalle, linea=None, columna=None)`

Guarda informacion de depuracion del escaneo.

Sirve para mostrar en la web el seguimiento del scanner.

### `reportar_error(mensaje, linea, columna)`

Registra un error lexico y lo agrega a la traza.

### `saltar_espacios_y_comentarios()`

Ignora:

- espacios
- tabs
- saltos de linea
- comentarios que empiezan con `#`

Estos elementos no se convierten en tokens.

### `leer_identificador_o_keyword()`

Reconoce:

- identificadores como `titulo` o `mensaje`
- palabras reservadas como:
  - `section`
  - `paragraph`
  - `itemize`
  - `item`
  - `bold`
  - `italic`
  - `color`
  - `upper`
  - `lower`

Si el lexema esta en la lista de palabras reservadas, se devuelve como keyword.
Si no, se devuelve como `ID`.

### `leer_numero()`

Reconoce numeros enteros y decimales simples.

### `leer_cadena()`

Reconoce textos entre comillas dobles.

Tambien valida:

- cadena sin cerrar
- escape invalido
- escape incompleto
- longitud maxima excedida

### `descartar_hasta_fin_de_literal()`

Se usa si una cadena falla por error grave.

Descarta hasta:

- una comilla de cierre
- un salto de linea
- el fin del archivo

### `sincronizar_error()`

Es la rutina de recuperacion del scanner.

Si aparece un simbolo invalido, avanza hasta un lugar donde ya pueda empezar otro token valido.

Normalmente se detiene al encontrar:

- espacio
- letra
- digito
- comilla
- delimitador simple como `(`, `)`, `,`, `;`, `=`, `+`

### `gettoken()`

Es la funcion principal del scanner.

Hace este flujo:

1. salta espacios y comentarios
2. revisa el siguiente caracter
3. reconoce el token correspondiente
4. si hay error, lo reporta y trata de recuperarse

### `scan_all()`

Lee toda la entrada hasta `EOF`.

### `escanear_fuente(fuente, max_literal_length=1024)`

Envuelve todo el proceso de escaneo y devuelve:

- tokens
- errores
- traza

---

## 4. Recuperacion de errores lexicos

El scanner usa una recuperacion tipo panic mode basica.

### Que hace cuando encuentra un error

1. reporta el error
2. descarta la parte invalida
3. busca un punto razonable para continuar
4. sigue escaneando

### Que simbolos usa para reanudar

Se considera que puede reanudar cuando aparece:

- espacio
- letra
- digito
- comilla
- delimitador simple

### Errores que detecta

- simbolo que no pertenece a ningun token
- cadena sin cerrar
- escape invalido dentro de una cadena
- escape incompleto
- literal demasiado largo

### Frase para explicar en clase

> El scanner implementa recuperacion lexico tipo panic mode: cuando detecta un simbolo invalido o una cadena mal formada, registra el error, descarta la parte problematica y avanza hasta encontrar un punto razonable para reanudar el escaneo.

---

## 5. Tokens que reconoce el scanner

### Palabras reservadas

- `section`
- `paragraph`
- `itemize`
- `item`
- `bold`
- `italic`
- `color`
- `upper`
- `lower`

### Delimitadores y simbolos simples

- `=`
- `+`
- `;`
- `,`
- `(`
- `)`

### Literales

- `ID`
- `STRING`
- `NUMBER`

### Fin de archivo

- `EOF`

---

## 6. Ejemplos de entradas validas

### Ejemplo 1: documento simple

```txt
section("Introduccion");
paragraph("Hola mundo desde el parser LR(1).");
```

### Ejemplo 2: negrita y cursiva

```txt
section("Formato");
paragraph("Esto es " + bold("negrita") + " y esto es " + italic("cursiva") + ".");
```

### Ejemplo 3: mayusculas y minusculas

```txt
section(upper("mini latex"));
paragraph("Texto en " + lower("MAYUSCULAS") + " convertido.");
```

### Ejemplo 4: colores reales

```txt
section("Colores");
paragraph(color("verde", "Este texto esta en verde"));
paragraph(color("rojo", "Este texto esta en rojo"));
```

### Ejemplo 5: lista

```txt
itemize(
  item("Primer punto"),
  item(bold("Segundo punto")),
  item(color("azul", "Tercer punto"))
);
```

### Ejemplo 6: mezcla con variables

```txt
titulo = upper("Mini Latex");
section(titulo);
paragraph("Hola " + color("verde", "mundo") + " desde el parser.");
```

---

## 7. Ejemplos de entradas invalidas

### Error 1: simbolo no reconocido

```txt
section("Hola");
paragraph("Texto invalido" @ "mas texto");
```

### Error 2: cadena sin cerrar

```txt
section("Hola mundo);
```

### Error 3: escape invalido

```txt
paragraph("Texto con escape \q invalido");
```

### Error 4: coma o parentesis mal puestos

```txt
paragraph(color("verde" "texto sin coma"));
```

### Error 5: entrada incompleta

```txt
itemize(item("uno"), item("dos"), item("tres");
```

### Error 6: sintaxis rota en varias partes

```txt
section("Titulo");
paragraph("Hola" + + bold("mundo"));
itemize(item("uno"), item(, "dos"));
```

---

## 8. Que esperar cuando pruebas errores

Cuando la entrada es invalida, el proyecto debe mostrar:

- errores del scanner
- errores del parser si la entrada llego a parser
- traza del scanner
- traza del parser

Eso es justamente lo que te conviene mostrar en la revision cuando te quieran romper el sistema.

---

## 9. Acciones ad hoc

Las acciones ad hoc no pertenecen al scanner, pero si forman parte del flujo completo del proyecto.

Se ejecutan en el parser cuando se reduce una produccion.

## Para que sirven

Sirven para traducir el documento mientras se analiza.

Por ejemplo:

- `section("Titulo")` genera un encabezado
- `paragraph("Texto")` genera un parrafo
- `bold("texto")` lo pone en negrita
- `italic("texto")` lo pone en cursiva
- `color("verde", "texto")` pinta el texto con el color indicado
- `itemize(...)` genera una lista

## Idea de funcionamiento

1. El scanner entrega tokens.
2. El parser reduce una produccion.
3. La accion ad hoc toma los valores de la reduccion.
4. Se construye parte del HTML final.
5. Al final se obtiene el documento traducido listo para visualizar o exportar.

## Frase para explicarlo en clase

> Las acciones ad hoc se ejecutan durante las reducciones del parser y permiten traducir el documento al mismo tiempo que se analiza, construyendo el HTML final de forma incremental.

---

## 10. Resumen corto para decirlo oralmente

> El scanner recorre el texto caracter por caracter con `peekchar()` y `getchar()`. Luego `gettoken()` reconoce identificadores, cadenas, numeros, palabras reservadas y simbolos simples. Si encuentra un error, usa `sincronizar_error()` o `descartar_hasta_fin_de_literal()` para recuperarse y continuar. Ademas, guarda una traza y una lista de errores para mostrarlos en la interfaz.
