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
    _main('./TESTS/Ugly.stipula')
    _main('./TESTS/Fill_Move.stipula')
    _main('./TESTS/Non_Liquid_Fill_Move.stipula')
    _main('./TESTS/AdvancedTest4.stipula')
    _main('./TESTS/Ping_Pong.stipula')
    _main('./TESTS/Bet.stipula')
    _main('./TESTS/Linear_Automaton.stipula')

# TODO
#   check dei local asset per ogni funzione
#   implementazione eventi
#   k-separate / complete
#   ci sono guardie/eventi
#   tipi di asset -> cosa farci?

# in compute_r : controllare per ogni evento se la funzione che lo inviocava è stata chiamata precedentemente nella computazione (basta mettere in event_visitor_entry l'id della funzione invocante e fare un check)
# oppure nell'oggetto abs_comp metti anche una lista di eventi che puoi chiamare (se la funz che contiene evento è stata invocata, aggiungo l'evento alla listam, appena chiamo l'evento, tolgo dalla lista (senza dover controlare il Count dell'evento, perche dipende linearmente da quante volte avevo chiamato la funzione "proprietaria", quindi se k=2, l'evento sara comunque chiamato al max 2 volte))