import sys
import antlr4

from generated.StipulaLexer import StipulaLexer
from generated.StipulaParser import StipulaParser

from classes.visitor import Visitor

def _main(file_path):
    input_stream = antlr4.FileStream(file_path)
    lexer = StipulaLexer(input_stream)
    stream = antlr4.CommonTokenStream(lexer)
    parser = StipulaParser(stream)
    tree = parser.stipula()

    if parser.getNumberOfSyntaxErrors() > 0:
        print('Syntax errors')
        sys.exit(1)
    Visitor().visit(tree)

if __name__ == '__main__':
    #_main('./TESTS/Bike_Rental_Refined.stipula')
    #_main('./TESTS/Ugly.stipula')
    _main('./TESTS/Fill_Move.stipula')
    #_main('./TESTS/AdvancedTest4.stipula')
    #_main('./TESTS/Ping_Pong.stipula')
    #_main('./TESTS/Bet.stipula')