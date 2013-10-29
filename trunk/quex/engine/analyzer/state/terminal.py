from quex.engine.analyzer.state.core import Processor

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
class TerminalState(Processor):
    __slots__ = ("action", "acceptance_id")
    def __init__(self, PatternId, PatternMatchAction):
        self.acceptance_id = PatternId
        self.action        = PatternMatchAction

class TerminalMatchState(Processor):
    def __init__(self, Pattern, UserCode, OnMatchCode, BeginOfLineSupportF, RequireTerminatingZero):
        Processor.__init__(self, state_index.get_terminal_state_index(PatternId), Entry())
        self.pattern                     = Pattern
        self.user_code                   = UserCode
        self.on_match_code               = OnMatchCode
        self.begin_of_line_support_f     = BeginOfLineSupportF
        self.terminating_zero_required_f = RequireTerminatingZero
        self.default_counter_required_f, \
        self.lc_count_code               = counter_for_pattern.get(self.pattern, EOF_ActionF)

    def get_code(self):
        lc_count_code = "".join(LanguageDB.REPLACE_INDENT(self.lc_count_code))

        if default_counter_required_f: 
            Mode.default_character_counter_required_f_set()

        # (*) THE user defined action to be performed in case of a match
        user_code, rtzp_f = get_code(CodeFragmentList, Mode)
        require_terminating_zero_preparation_f = require_terminating_zero_preparation_f or rtzp_f

        store_last_character_str = ""
        if BeginOfLineSupportF:
            # IDEA (TODO): The character before lexeme start does not have to be
            # written into a special register. Simply, make sure that
            # '_lexeme_start_p - 1' is always in the buffer. This may include that
            # on the first buffer load '\n' needs to be at the beginning of the
            # buffer before the content is loaded. Not so easy; must be carefully
            # approached.
            store_last_character_str = "    %s\n" % LanguageDB.ASSIGN("me->buffer._character_before_lexeme_start", 
                                                                      LanguageDB.INPUT_P_DEREFERENCE(-1))

        set_terminating_zero_str = ""
        if rtzp_f:
            set_terminating_zero_str += "    QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"

        txt  = ""
        txt += lc_count_code
        txt += store_last_character_str
        txt += set_terminating_zero_str
        txt += on_match_code
        txt += "    {\n"
        txt += user_code
        txt += "\n    }"

class TerminalInterim(Processor):
   __slots__ = ("target_terminal_index",)
   def __init__(self, TargetTerminalIndex):
       self.target_terminal_index = TargetTerminalIndex

   def get_code(self):
       LanguageDB = Setup.language_db
       return LanguageDB.GOTO_BY_DOOR_ID(DoorID(self.target_terminal_index, 0))


