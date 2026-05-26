
## Ejemplos que debe aceptar
- `bold("Hola") + "Mundo" + 125 + id`
- `x = italic("Hola") + 12`
- `resultado = color("Rojo") + upper(nombre)`
- `texto = lower("HOLA") + " mundo"`

## Gramática

TERMINALES: ID STRING NUMBER = + ; ( ) bold italic color upper lower

NO_TERMINALES: Program StmtList Stmt Expr ExprTail Term Factor FuncCall FunctionName Literal

INICIAL: Program

PRODUCCIONES:

Program -> StmtList
StmtList -> Stmt ; StmtList | Stmt
Stmt -> ID = Expr | Expr
Expr -> Term ExprTail
ExprTail -> + Term ExprTail | ε
Term -> Factor
Factor -> FuncCall | Literal | ID | ( Expr )
FuncCall -> FunctionName ( Expr )
FunctionName -> bold | italic | color | upper | lower
Literal -> STRING | NUMBER
