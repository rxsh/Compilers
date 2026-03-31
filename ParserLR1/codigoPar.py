

def _tokenizar_lista(texto):
    tokens = []
    for t in texto.split():
        if t == "()":
            tokens.append("(")
            tokens.append(")")
        else:
            tokens.append(t)
    return tokens


def leer_gramatica(ruta):
    terminales = []
    no_terminales = []
    inicial = None
    producciones = []
    en_producciones = False

    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue

            if linea.startswith("TERMINALES:"):
                datos = linea.split(":", 1)[1].strip()
                terminales = _tokenizar_lista(datos)
                en_producciones = False
                continue

            if linea.startswith("NO_TERMINALES:"):
                datos = linea.split(":", 1)[1].strip()
                no_terminales = datos.split()
                en_producciones = False
                continue

            if linea.startswith("INICIAL:"):
                inicial = linea.split(":", 1)[1].strip()
                en_producciones = False
                continue

            if linea.startswith("PRODUCCIONES:"):
                en_producciones = True
                continue

            if en_producciones:
                lado_izq, lado_der = linea.split("->")
                lado_izq = lado_izq.strip()
                alternativas = lado_der.split("|")
                for alt in alternativas:
                    simbolos_der = alt.strip().split()
                    producciones.append((lado_izq, simbolos_der))

    return terminales, no_terminales, inicial, producciones


if __name__ == "__main__":
    terminales, no_terminales, inicial, producciones = leer_gramatica("gramatica.txt")
    print("Terminales:", terminales)
    print("No terminales:", no_terminales)
    print("Inicial:", inicial)
    print("Producciones:")
    for p in producciones:
        print(p)
