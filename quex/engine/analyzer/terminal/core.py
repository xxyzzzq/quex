from   quex.engine.analyzer.state.core  import Processor
from   quex.engine.analyzer.state.entry import Entry
import quex.engine.state_machine.index  as index

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
class TerminalPlainCode(Processor):
    def __init__(self, IncidenceId, TheCodeFragment):
        Processor.__init__(self, index.map_incidence_id_to_state_index(IncidenceId), Entry())
        self.__incidence_id  = IncidenceId
        self.__code_fragment = TheCodeFragment

    def incidence_id(self):
        return self.__incidence_id

    @property
    def code_fragment(self):
        return self.__code_fragment

    def get_code(self):
        return self.__code_fragment.get_code()

class TerminalInterim(Processor):
   __slots__ = ("target_terminal_index",)
   def __init__(self, TargetTerminalIndex):
       self.target_terminal_index = TargetTerminalIndex

   def get_code(self):
       LanguageDB = Setup.language_db
       return LanguageDB.GOTO_BY_DOOR_ID(DoorID(self.target_terminal_index, 0))


