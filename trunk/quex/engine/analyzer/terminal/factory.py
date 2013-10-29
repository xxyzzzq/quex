from quex.engine.analyzer.state.terminal.core import TerminalState, \
                                                TerminalMatchState
                E_IncidenceIDs.SKIP:              TerminalSkipCharacterSet(command_list),
                E_IncidenceIDs.SKIP_RANGE:        TerminalSkipRange(command_list),
                E_IncidenceIDs.SKIP_NESTED_RANGE: TerminalSkipNestedRange(command_list),
                E_IncidenceIDs.INDENTATION:       TerminalIndentationHandler(command_list),
from quex.blackboard import E_IncidenceIDs

import re

Match_Lexeme = re.compile("\\bLexeme\\b", re.UNICODE)

class TerminalStateFactory:
    def __init__(Mode, IndentationSupportF, BeginOfLineSupportF):
        self.code_dedicated_indentation_handler     = self.get_code_dedicated_indentation_handler(Mode, 
                                                                                                  IndentationSupportF)
        self.code_store_last_character              = self.get_code_store_last_character(BeginOfLineSupportF)

        self.code_on_match,          \
        self.rtz_on_match_f          = self.collect_code(Mode.incidence_db[E_IncidenceIDs.MATCH], Mode) 
        self.code_on_after_match,    \
        self.rtz_on_after_match_f    = self.collect_code(Mode.incidence_db[E_IncidenceIDs.AFTER_MATCH], Mode)
        self.on_end_of_stream_action = self.do_OnEndOfStream()
        self.on_failure_action       = self.do_OnFailure()

    def do(self, Incidence, action):
        if isinstance(incidence_id, (int, long)):
            terminal = TerminalMatchState(command_list)
        else:
            terminal = {
                E_IncidenceIDs.SKIP:              TerminalSkipCharacterSet(command_list),
                E_IncidenceIDs.SKIP_RANGE:        TerminalSkipRange(command_list),
                E_IncidenceIDs.SKIP_NESTED_RANGE: TerminalSkipNestedRange(command_list),
                E_IncidenceIDs.INDENTATION:       TerminalIndentationHandler(command_list),
            }[incidence_id]

    def do_OnEndOfStream(self, IncidenceDb):
        if IncidenceDb.has_key(E_IncidenceIDs.END_OF_STREAM):
            code_fragment_list = IncidenceDb[E_IncidenceIDs.END_OF_STREAM]
        else:
            # We cannot make any assumptions about the token class, i.e. whether
            # it can take a lexeme or not. Thus, no passing of lexeme here.
            txt  = "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
            txt += "RETURN;\n"
            code_fragment_list = [ CodeFragment(txt) ]

        code_fragment_list.insert(0, self.dedicated_indentation_handler_code)


        # RETURNS: end_of_stream_action, db 
        result = self.prepare_CodeFragment(Mode, code_fragment_list, None, EOF_ActionF=True)

        return PatternActionInfo(E_IncidenceIDs.END_OF_STREAM, result)

    def do_OnFailure(self, IncidenceDb):
        if IncidenceDb.has_key(E_IncidenceIDs.FAILURE):
            code_fragment_list = IncidenceDb[E_IncidenceIDs.FAILURE]
        else:
            txt  = "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % Mode.name 
            txt += "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
            txt += "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
            code_fragment_list = [ CodeFragment(txt) ]

        # RETURNS: on_failure_action, db 
        prepared_code = self.prepare_CodeFragment(Mode, code_fragment_list, None, Failure_ActionF=True) 

        txt = [
            1,     "if(QUEX_NAME(Buffer_is_end_of_file)(&me->buffer)) {\n",
            2,         "/* Init state is going to detect 'input == buffer limit code', and\n",
            2,         " * enter the reload procedure, which will decide about 'end of stream'. */\n",
            1,     "} else {\n",
            2,         "/* In init state 'input = *input_p' and we need to increment\n",
            2,         " * in order to avoid getting stalled. Else, input = *(input_p - 1),\n",
            2,         " * so 'input_p' points already to the next character.                   */\n",
            2,         "if( me->buffer._input_p == me->buffer._lexeme_start_p ) {\n",
            3,               "/* Step over non-matching character */\n",
            3,               "%s\n" % LanguageDB.INPUT_P_INCREMENT(),
            2,         "}\n",
            1,     "}\n",
            1,     "%s\n"     % prepared_code.get_code_string(), 
            1,     "goto %s;" % Label.global_reentry_preparation_2(GotoedF=True)
        ]

        return PatternActionInfo(E_IncidenceIDs.FAILURE, CodeFragment(txt))

    def prepare_CodeFragment(self, Mode, CodeFragmentList, ThePattern, Failure_ActionF=False, EOF_ActionF=False):
        """-- If there are multiple handlers for a single event they are combined
        
           -- Adding debug information printer (if desired)
        
           -- The task of this function is it to adorn the action code for each pattern with
              code for line and column number counting.
        """
        assert Mode.__class__.__name__  == "Mode"
        assert ThePattern      is None or ThePattern.__class__.__name__ == "Pattern" 
        assert type(Failure_ActionF)    == bool
        assert type(EOF_ActionF)        == bool

        code_on_match, rtz_on_match_f = self.get_code_on_match(Failure_ActionF)
        code_user, rtz_user_f         = self.collect_code(CodeFragmentList, Mode)
        code_line_column_counter      = self.get_code_line_column_count(ThePattern, EOF_ActionF)
        code_store_last_character     = self.code_store_last_character

        require_terminating_zero_f    = rtz_on_match_f | rtz_user_f | self.rtz_on_after_match_f

        code_terminating_zero         = self.get_code_terminating_zero(require_terminating_zero_f)

        return CodeFragment([
            code_line_column_counter,
            code_store_last_character,
            code_terminating_zero,
            code_on_match,
            "{\n",
            code_user,
            "\n}",
        ])

    def collect_code(CodeFragmentList, Mode=None):
        global Match_Lexeme 
        LanguageDB = Setup.language_db
        if len(CodeFragmentList) == 0:
            return "", False

        code_list = []
        for fragment in CodeFragmentList:
            code_list.extend(fragment.get_code(Mode))

        code_str = "".join(LanguageDB.GET_PLAIN_STRINGS(code_list))

        # If 'Lexeme' occurs as an isolated word, then ensure the generation of 
        # a terminating zero. Note, that the occurence of 'LexemeBegin' does not
        # ensure the preparation of a terminating zero.
        require_terminating_zero_preparation_f = (Match_Lexeme.search(code_str) is not None) 

        return pretty_code(code_str, IndentationBase), \
               require_terminating_zero_preparation_f

    def get_code_on_match(self, Failure_ActionF):
        if Failure_ActionF:   # OnFailure == 'nothing matched'; 
            return "", False  # => 'on_match_code' is inappropriate.
        return self.code_on_match, self.rtz_on_match_f

    def get_code_terminating_zero(self, RequireTerminatingZeroF):
        if not RequireTerminatingZeroF:
            return ""
        return "    QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"

    def get_code_line_column_count(self, ThePattern, EOF_ActionF):
        default_counter_required_f, \
        result                      = counter_for_pattern.get(ThePattern, EOF_ActionF)
        result                      = "".join(LanguageDB.REPLACE_INDENT(lc_count_code))
        if default_counter_required_f: 
            Mode.default_character_counter_required_f_set()
        return result

    def get_code_dedicated_indentation_handler(IndentationSupportF, Mode):
        if not IndentationSupportF: 
            return ""
        if Mode.default_indentation_handler_sufficient():
            return "    QUEX_NAME(on_indentation)(me, /*Indentation*/0, LexemeNull);\n"
        else:
            return "    QUEX_NAME(%s_on_indentation)(me, /*Indentation*/0, LexemeNull);\n" % Mode.name

    def get_code_store_last_character(self, BeginOfLineSupportF):
        if not BeginOfLineSupportF:
            return ""
        # TODO: The character before lexeme start does not have to be written
        # into a special register. Simply, make sure that '_lexeme_start_p - 1'
        # is always in the buffer. This may include that on the first buffer
        # load '\n' needs to be at the beginning of the buffer before the
        # content is loaded. Not so easy; must be carefully approached.
        return "    %s\n" % LanguageDB.ASSIGN("me->buffer._character_before_lexeme_start", 
                                              LanguageDB.INPUT_P_DEREFERENCE(-1))


