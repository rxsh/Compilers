# Explicacion Simple Para La Presentacion

Este documento resume el proyecto de forma corta y clara.

---

## 1. Scanner

El scanner lee el texto caracter por caracter y lo convierte en tokens.

Un token es una pieza basica del lenguaje, por ejemplo:

- `section`
- `paragraph`
- `ID`
- `STRING`
- `NUMBER`
- `(`
- `)`
- `,`
- `;`

### Que hace cada parte

- `peekchar()` mira el siguiente caracter sin mover la posicion.
- `getchar()` consume un caracter y avanza.
- `gettoken()` decide que token devolver.
- `saltar_espacios_y_comentarios()` ignora espacios y comentarios.
- `leer_identificador_o_keyword()` reconoce palabras reservadas e identificadores.
- `leer_cadena()` reconoce textos entre comillas.
- `leer_numero()` reconoce numeros.
- `sincronizar_error()` ayuda a recuperarse si aparece un simbolo invalido.

### Que errores detecta el scanner

- simbolo invalido
- cadena sin cerrar
- escape invalido
- escape incompleto
- cadena demasiado larga

### Frase corta para decir

> El scanner transforma el texto fuente en tokens y si encuentra un error lexico, lo reporta y avanza hasta un punto donde puede seguir leyendo.

---

## 2. Recuperacion de errores en el scanner

Cuando el scanner ve un caracter que no pertenece al lenguaje:

1. muestra el error
2. descarta ese fragmento
3. busca un lugar seguro para continuar
4. sigue escaneando

Eso es una recuperacion basica tipo panic mode lexico.

### Frase corta para decir

> El scanner usa recuperacion tipo panic mode: descarta lo invalido y sigue desde un punto seguro.

---

## 3. Parser LR(1)

El parser recibe los tokens del scanner y decide si la cadena es valida usando una tabla LR(1).

### Que hace

- consulta `ACTION`
- consulta `GOTO`
- hace `shift`
- hace `reduce`
- acepta o rechaza la cadena
- construye el arbol de parseo

### Funciones clave

- `closure()`: completa un conjunto de items LR(1).
- `ir_a()`: mueve el punto y calcula la siguiente cerradura.
- `coleccion_canonica_lr1()`: construye los estados LR(1).
- `construir_tabla_lr1()`: arma las tablas `ACTION` y `GOTO`.
- `parsear_lr1()`: hace el parseo paso a paso.

### Frase corta para decir

> El parser LR(1) revisa la tabla ACTION/GOTO para decidir si desplazar, reducir o aceptar la entrada.

---

## 4. Recuperacion de errores en el parser

Si el parser no encuentra `ACTION[estado, token]`, entra en recuperacion.

### Que hace

1. detecta el error
2. registra el error
3. hace pop de la pila hasta encontrar un estado util
4. busca un no terminal de recuperacion
5. avanza la entrada hasta un token sincronizador
6. continua el analisis

Si el mismo token sigue causando el mismo error, el parser lo descarta una vez para no quedarse atascado.

### En que se basa la sincronizacion

Se usa `FOLLOW(no_terminal) ∪ {$}`.

### Frase corta para decir

> El parser usa panic mode sintactico: cuando no hay accion valida, retrocede en la pila, sincroniza con `FOLLOW` y sigue.

---

## 5. Acciones ad hoc

Las acciones ad hoc son las reglas que traducen el documento mientras se hace el parseo.

### Para que sirven

Permiten convertir la entrada a un documento HTML final.

### Ejemplos

- `section("Titulo")` genera un encabezado
- `paragraph("Texto")` genera un parrafo
- `bold("texto")` pone negrita
- `italic("texto")` pone cursiva
- `color("verde", "texto")` pinta el texto de verde
- `itemize(...)` genera una lista

### Frase corta para decir

> Las acciones ad hoc se ejecutan en las reducciones del parser y permiten construir la traduccion del documento al mismo tiempo que se analiza.

---

## 6. Resumen muy corto

> El scanner convierte el texto en tokens, el parser LR(1) decide si la estructura es valida y las acciones ad hoc traducen el documento mientras se analiza. Si algo falla, tanto el scanner como el parser tienen recuperacion de errores para seguir mostrando el resto de la entrada.
