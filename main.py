import sys
import antlr4
import click
from pathlib import Path

from generated.StipulaLexer import StipulaLexer
from generated.StipulaParser import StipulaParser
from classes.liquidity_visitor import LiquidityVisitor

def run(file_path: str, function_frequency: int, is_verbose: bool = False):
    input_stream = antlr4.FileStream(file_path)
    lexer = StipulaLexer(input_stream)
    stream = antlr4.CommonTokenStream(lexer)
    parser = StipulaParser(stream)
    tree = parser.stipula()

    if parser.getNumberOfSyntaxErrors() > 0:
        print('Syntax errors')
        sys.exit(1)
    visitor = LiquidityVisitor(function_frequency, is_verbose)
    visitor.visit(tree)

@click.command()
@click.argument("file_path", default="./TESTS")
@click.argument("function_frequency", default=3)
@click.option("-v", "--verbose", "is_verbose", default=True, show_default=True, is_flag=True, help='Show verbose output.')
def cli_main(file_path, function_frequency, is_verbose):
    path = Path(file_path)

    if path.is_file():
        if path.suffix == ".stipula":
            run(file_path, function_frequency, is_verbose)
        else:
            raise ValueError(f"File type '{path.suffix}' is not supported.")
    elif path.is_dir():
        for stipula_file in path.rglob("*.stipula"):
            run(stipula_file, function_frequency, is_verbose)
    else:
        raise ValueError(f"Path does not exist: {path}")

if __name__ == "__main__":
    cli_main()