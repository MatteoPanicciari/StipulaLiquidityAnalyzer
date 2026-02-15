import sys
import antlr4
import click
from pathlib import Path

from generated.StipulaLexer import StipulaLexer
from generated.StipulaParser import StipulaParser
from classes.liquidity_visitor import LiquidityVisitor

def run(file_path: str, is_verbose: bool = False):
    input_stream = antlr4.FileStream(file_path)
    lexer = StipulaLexer(input_stream)
    stream = antlr4.CommonTokenStream(lexer)
    parser = StipulaParser(stream)
    tree = parser.stipula()

    if parser.getNumberOfSyntaxErrors() > 0:
        print('Syntax errors')
        sys.exit(1)
    visitor = LiquidityVisitor(is_verbose)
    visitor.visit(tree)

@click.command()
@click.argument("file_path", default="./TESTS")
@click.option("-v", "--verbose", "is_verbose", type=bool, default=False, show_default=True, is_flag=True, help='Show verbose output.')
def cli_main(file_path, is_verbose):
    path = Path(file_path)

    if path.is_file():
        if path.suffix == ".stipula":
            run(file_path, is_verbose)
        else:
            raise ValueError(f"File type '{path.suffix}' is not supported.")
    elif path.is_dir():
        for stipula_file in path.rglob("*.stipula"):
            run(stipula_file, is_verbose)
    else:
        raise ValueError(f"Path does not exist: {path}")

if __name__ == "__main__":
    cli_main()

# TODO
#   togliere(?) i visitExpression dato che non devo assicurarmi dei tipi o degli id
#   capire se va bene usare il complete algorithm se anche una sola abs_comp in un contratto ha i tipi di asset che non sono singoletti
#   capire se gli algoritmi di tqk e liquidity sono effettivamente come devono essere per costo computazionale
#   testare all'infinito
#   gestire meglio gli errori (es: chiamo il get_field_value con un field inesistente, lo devo gestire io?)
#   mettere k tra l'input?
#   fare i pytest