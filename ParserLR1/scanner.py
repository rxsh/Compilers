from dataclasses import dataclass, asdict


EOF = "$"
KEYWORDS = {
    "bold",
    "italic",
    "color",
    "upper",
    "lower",
    "section",
    "paragraph",
    "itemize",
    "item",
}
SINGLE_CHAR_TOKENS = {
    "=": "=",
    "+": "+",
    ";": ";",
    ",": ",",
    "(": "(",
    ")": ")",
}
VALID_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int

    def a_dict(self):
        return asdict(self)


@dataclass
class ScannerError:
    mensaje: str
    linea: int
    columna: int

    def a_dict(self):
        return asdict(self)


class Scanner:
    def __init__(self, fuente, max_literal_length=1024):
        self.fuente = fuente
        self.max_literal_length = max_literal_length
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.errores = []
        self.traza = []

    def eof(self):
        return self.pos >= len(self.fuente)

    def peekchar(self):
        if self.eof():
            return None
        return self.fuente[self.pos]

    def getchar(self):
        if self.eof():
            return None

        ch = self.fuente[self.pos]
        self.pos += 1

        if ch == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1

        return ch

    def agregar_traza(self, evento, detalle, linea=None, columna=None):
        self.traza.append(
            {
                "evento": evento,
                "detalle": detalle,
                "linea": self.linea if linea is None else linea,
                "columna": self.columna if columna is None else columna,
            }
        )

    def reportar_error(self, mensaje, linea, columna):
        self.errores.append(ScannerError(mensaje, linea, columna))
        self.agregar_traza("error", mensaje, linea, columna)

    def descartar_hasta_fin_de_literal(self):
        while True:
            ch = self.peekchar()
            if ch is None:
                return
            if ch == "\n":
                return
            if ch == '"':
                self.getchar()
                return
            self.getchar()

    def saltar_espacios_y_comentarios(self):
        while True:
            ch = self.peekchar()
            if ch is None:
                return

            if ch in " \t\r\n":
                self.getchar()
                continue

            if ch == "#":
                linea, columna = self.linea, self.columna
                comentario = []
                while self.peekchar() not in (None, "\n"):
                    comentario.append(self.getchar())
                self.agregar_traza("comentario", "".join(comentario), linea, columna)
                continue

            return

    def leer_identificador_o_keyword(self):
        linea, columna = self.linea, self.columna
        lexema = []

        while True:
            ch = self.peekchar()
            if ch is None or not (ch.isalnum() or ch == "_"):
                break
            lexema.append(self.getchar())

        lexema = "".join(lexema)
        tipo = lexema if lexema in KEYWORDS else "ID"
        token = Token(tipo, lexema, linea, columna)
        self.agregar_traza("token", f"{tipo} -> {lexema}", linea, columna)
        return token

    def leer_numero(self):
        linea, columna = self.linea, self.columna
        lexema = []
        tiene_punto = False

        while True:
            ch = self.peekchar()
            if ch is None:
                break
            if ch.isdigit():
                lexema.append(self.getchar())
                continue
            if ch == "." and not tiene_punto:
                tiene_punto = True
                lexema.append(self.getchar())
                continue
            break

        lexema = "".join(lexema)
        token = Token("NUMBER", lexema, linea, columna)
        self.agregar_traza("token", f"NUMBER -> {lexema}", linea, columna)
        return token

    def leer_cadena(self):
        linea, columna = self.linea, self.columna
        self.getchar()
        contenido = []
        lexema = ['"']

        while True:
            ch = self.peekchar()

            if ch is None:
                self.reportar_error(
                    "Cadena sin cerrar antes de fin de archivo",
                    linea,
                    columna,
                )
                return None

            if ch == "\n":
                self.reportar_error(
                    "Cadena sin cerrar antes de fin de linea",
                    linea,
                    columna,
                )
                return None

            if ch == '"':
                lexema.append(self.getchar())
                break

            if ch == "\\":
                lexema.append(self.getchar())
                escape = self.peekchar()
                if escape is None:
                    self.reportar_error(
                        "Escape incompleto al final de archivo",
                        self.linea,
                        self.columna,
                    )
                    return None
                if escape not in VALID_ESCAPES:
                    self.reportar_error(
                        f"Escape invalido \\{escape}",
                        self.linea,
                        self.columna,
                    )
                    lexema.append(self.getchar())
                    self.descartar_hasta_fin_de_literal()
                    return None
                lexema.append(self.getchar())
                contenido.append(VALID_ESCAPES[escape])
            else:
                lexema.append(self.getchar())
                contenido.append(ch)

            if len(contenido) > self.max_literal_length:
                self.reportar_error(
                    f"Cadena supera el maximo permitido de {self.max_literal_length} caracteres",
                    linea,
                    columna,
                )
                self.descartar_hasta_fin_de_literal()
                return None

        token = Token("STRING", "".join(lexema), linea, columna)
        self.agregar_traza("token", f"STRING -> {token.lexema}", linea, columna)
        return token

    def sincronizar_error(self):
        while True:
            ch = self.peekchar()
            if ch is None:
                return
            if ch.isspace() or ch in SINGLE_CHAR_TOKENS or ch == "#" or ch.isalpha() or ch == "_" or ch.isdigit() or ch == '"':
                return
            self.getchar()

    def gettoken(self):
        while True:
            self.saltar_espacios_y_comentarios()

            if self.eof():
                token = Token(EOF, EOF, self.linea, self.columna)
                self.agregar_traza("token", f"{EOF} -> {EOF}", self.linea, self.columna)
                return token

            ch = self.peekchar()
            linea, columna = self.linea, self.columna

            if ch.isalpha() or ch == "_":
                return self.leer_identificador_o_keyword()

            if ch.isdigit():
                return self.leer_numero()

            if ch == '"':
                token = self.leer_cadena()
                if token is not None:
                    return token
                self.sincronizar_error()
                continue

            if ch in SINGLE_CHAR_TOKENS:
                self.getchar()
                tipo = SINGLE_CHAR_TOKENS[ch]
                token = Token(tipo, ch, linea, columna)
                self.agregar_traza("token", f"{tipo} -> {ch}", linea, columna)
                return token

            self.reportar_error(
                f"Simbolo no reconocido '{ch}'",
                linea,
                columna,
            )
            self.getchar()
            self.sincronizar_error()

    def scan_all(self):
        tokens = []
        while True:
            token = self.gettoken()
            tokens.append(token)
            if token.tipo == EOF:
                break
        return tokens


def escanear_fuente(fuente, max_literal_length=1024):
    scanner = Scanner(fuente, max_literal_length=max_literal_length)
    tokens = scanner.scan_all()
    return {
        "tokens": [token.a_dict() for token in tokens],
        "errores": [error.a_dict() for error in scanner.errores],
        "traza": scanner.traza,
    }
