import sys
import antlr4

from generated.StipulaLexer import StipulaLexer
from generated.StipulaParser import StipulaParser

from classes.liquidity_visitor import LiquidityVisitor

def _main(file_path: str, is_verbose: bool=True):
    input_stream = antlr4.FileStream(file_path)
    lexer = StipulaLexer(input_stream)
    stream = antlr4.CommonTokenStream(lexer)
    parser = StipulaParser(stream)
    tree = parser.stipula()

    if parser.getNumberOfSyntaxErrors() > 0:
        print('Syntax errors')
        sys.exit(1)
    LiquidityVisitor(is_verbose).visit(tree)

if __name__ == '__main__':
    #_main('./TESTS/Ugly.stipula')
    _main('./TESTS/Fill_Move.stipula')
    _main('./TESTS/Non_Liquid_Fill_Move.stipula')
    #_main('TESTS/AbsCompTest.stipula')
    #_main('./TESTS/Ping_Pong.stipula')
    #_main('./TESTS/Bet.stipula')
    #_main('./TESTS/Linear_Automaton.stipula')

# commentare
# togliere (?) i visitExpression dato che non devo assicurarmi dei tipi o degli id
# capire se va bene usare il complete algorithm se anche una sola abs_comp in un contratto ha i tipi di asset che non sono singoletti
# mettere il mio codice nel progetto di erik