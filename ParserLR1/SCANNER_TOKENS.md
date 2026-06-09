# Scanner del Lenguaje

## Tokens definidos

- `ID`
  Identificadores de usuario.
  Patron: letra o `_` seguido de letras, digitos o `_`.

- `STRING`
  Literales entre comillas dobles.
  Soporta escapes: `\\`, `\"`, `\n`, `\t`, `\r`.

- `NUMBER`
  Literales numericos enteros o decimales simples.

- `=`
  Asignacion.

- `+`
  Concatenacion o suma segun el contexto del lenguaje.

- `;`
  Separador de sentencias.

- `(`
  Apertura de parametros o subexpresion.

- `)`
  Cierre de parametros o subexpresion.

- `bold`
- `italic`
- `color`
- `upper`
- `lower`
  Palabras reservadas para funciones del lenguaje.

- `$`
  Fin de archivo para el parser.

## Comentarios

Se usa `#` para comentario de linea.
El scanner los ignora y no emite token.

## Espacios en blanco

Espacios, tabulaciones y saltos de linea se descartan por el scanner.

## Errores lexicos que se manejan

- Simbolo no reconocido
- Cadena sin cerrar
- Escape invalido dentro de cadena
- Escape incompleto al final del archivo
- Literales que exceden el tamano maximo

## Observacion sobre la gramatica

La gramatica actual modela el contenido textual a traves de `STRING`.
Si mas adelante quieres texto libre fuera de comillas, habria que agregar
un token como `TEXT` y ajustar la gramatica para distinguir texto, marcas y comandos.
