from   quex.engine.analyzer.state.core  import Processor
from   quex.engine.analyzer.state.entry import Entry
import quex.engine.state_machine.index  as index
from   quex.engine.tools                import typed

#__________________________________________________________________________
#
# TerminalState:
#                    .-------------------------------------------------.
#  .-----.           |                                                 |
#  | 341 |--'accept'--> input_p = position[2]; --->---+---------.      |
#  '-----'           |  set terminating zero;         |         |      |
#  .-----.           |                                |    .---------. |
#  | 412 |--'accept'--> column_n += length  ------>---+    | pattern | |
#  '-----'           |  set terminating zero;         |    |  match  |--->
#  .-----.           |                                |    | actions | |
#  | 765 |--'accept'--> line_n += 2;  ------------>---'    '---------' |
#  '-----'           |  set terminating zero;                          |
#                    |                                                 |
#                    '-------------------------------------------------'
# 
# A terminal state prepares the execution of the user's pattern match 
# actions and the start of the next analysis step. For this, it computes
# line and column numbers, sets terminating zeroes in strings and resets
# the input pointer to the position where the next analysis step starts.
#__________________________________________________________________________
class Terminal(Processor):
    @typed(Name=(str,unicode), LexemeBeginRequiredF=bool, Code=list)
    def __init__(self, IncidenceId, Code, Name="", LexemeBeginRequiredF=False):
        Processor.__init__(self, index.map_incidence_id_to_state_index(IncidenceId), Entry())
        self.__incidence_id            = IncidenceId
        self.__code                    = Code
        self.__name                    = Name
        self.__lexeme_begin_required_f = LexemeBeginRequiredF

    def incidence_id(self):
        return self.__incidence_id

    def name(self):
        return self.__name

    def code(self):
        return self.__code

    def lexeme_begin_required_f(self):
        return self.__lexeme_begin_required_f

