
def tokenizar_lista(texto):

    tokens = []
    for t in texto.split():
        if t == "()":
            tokens.append("(")
            tokens.append(")")
        else:
            tokens.append(t)
    
    return tokens

def leer_gramatica(ruta):

    producciones = []
    terminales = []
    no_terminales = []
    inicial = None
    en_producciones = False

    with open(ruta,"r", encoding="UTF-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue

            if linea.startswith("TERMINALES:"):
                datos = linea.split(":",1)[1].strip()
                terminales = tokenizar_lista(datos)
                en_producciones = False
                continue

            if linea.startswith("NO_TERMINALES:"):
                datos = linea.split(":",1)[1].strip()
                no_terminales = tokenizar_lista(datos)
                en_producciones = False
                continue

            if linea.startswith("INICIAL:"):
                inicial = linea.split(":",1)[1].strip()
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
                    producciones.append((lado_izq,simbolos_der))

    return terminales, no_terminales, inicial, producciones

def calcular_first(terminales, no_terminales, producciones):

    EPSILON = "ε"
    EOF = "$"
    
    first = {}

    for t in terminales + [EOF, EPSILON]:
        first[t] = {t}

    for nt in no_terminales:
        first[nt] = set()

    cambio = True
    while cambio:
        cambio = False

        for A,B in producciones:
            rhs = set()
            i = 0

            while i < len(B):
                simbolo = B[i]
                rhs.update(first[simbolo] - {EPSILON})

                if EPSILON in first[simbolo]:
                    i += 1
                else:
                    break

            if i == len(B):
                rhs.add(EPSILON)

            antes = len(first[A])
            first[A].update(rhs)
            if len(first[A]) > antes:
                cambio = True

    return first

def calcular_follow(no_terminales, producciones, inicial, first):

    EPSILON = "ε"
    EOF = "$"

    follow = {}

    for A in no_terminales:
        follow[A] = set()

    follow[inicial].add(EOF)

    cambio = True
    while cambio:
        cambio = False

        for A,B in producciones:
            trailer = follow[A].copy()

            for i in range(len(B) - 1, -1, -1):
                simbolo = B[i]

                if simbolo in no_terminales:
                    antes = len(follow[simbolo])
                    follow[simbolo].update(trailer)
                    if len(follow[simbolo]) > antes:
                        cambio = True

                    if EPSILON in first[simbolo]:
                        trailer = trailer.union(first[simbolo] - {EPSILON})
                    else:
                        trailer = first[simbolo].copy()
                else:
                    trailer = first[simbolo].copy()


    return follow



if __name__ == "__main__":

    terminales, no_terminales, inicial, producciones = leer_gramatica("gramatica.txt")
    print(f"Terminales: {terminales}")
    print(f"No Terminales: {no_terminales}")
    print(f"Inicial: {inicial}")
    print("Producciones: ")
    for p in producciones:
        print(p)


    print("----------------")
    first = calcular_first(terminales, no_terminales, producciones)
    follow = calcular_follow(no_terminales, producciones, inicial, first)
    
    print("FIRST:")
    for simbolo in first:
        print(simbolo, "=", first[simbolo])

    print("\nFOLLOW:")
    for simbolo in follow:
        print(simbolo, "=", follow[simbolo])