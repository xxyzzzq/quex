"""Action Preparation:

Functions to prepare a source code fragment to be sticked into the lexical
analyzer. This includes the following:

-- pattern matches: 

   (optional) line and column counting based on the character content of the
   lexeme. Many times, the character or line number count is determined by the
   pattern, so counting can be replaced by an addition of a constant (or even
   no count at all).
                        
-- end of file/stream action:

   If not defined by the user, send 'TERMINATION' token and return.

-- failure action (no match):

   If not defined by the user, abort program with a message that tells that the
   user did not define an 'on_failure' handler.

(C) 2005-2012 Frank-Rene Schaefer
"""
from   quex.engine.generator.action_info           import CodeFragment, \
                                                          PatternActionInfo
from   quex.engine.analyzer.door_id_address_label  import Label
from   quex.blackboard                             import setup as Setup, E_ActionIDs
import quex.output.cpp.counter_for_pattern         as     counter_for_pattern

import re

LanguageDB   = None
Match_Lexeme = re.compile("\\bLexeme\\b", re.UNICODE)

class TerminalStateFactory:
    def __init__(Mode, IndentationSupportF, BeginOfLineSupportF):
        self.indentation_support_f                  = IndentationSupportF
        self.begin_of_line_support_f                = BeginOfLineSupportF
        self.require_terminating_zero_preparation_f = False

        self.on_match                = self.do_OnMatch()
        self.on_after_match          = self.do_OnAfterMatch()
        self.on_end_of_stream_action = self.do_OnEndOfStream()
        self.on_failure_action       = self.do_OnFailure()

        self.indentation_counter_terminal_id = Mode.get_indentation_counter_terminal_index()

    def do_OnMatch(self):
        if not Mode.has_code_fragment_list("on_match"):
            return ""
        result = self.collect_code(Mode.get_code_fragment_list("on_match"), Mode)
        return result

    def do_OnAfterMatch(self):
        if not Mode.has_code_fragment_list("on_after_match"):
            return None, False
        result = self.collect_code(Mode.get_code_fragment_list("on_after_match"), Mode)

        return PatternActionInfo(E_ActionIDs.ON_AFTER_MATCH, CodeFragment(result))

    def do_OnEndOfStream(self):
        if Mode.has_code_fragment_list("on_end_of_stream"):
            code_fragment_list = Mode.get_code_fragment_list("on_end_of_stream")
        else:
            # We cannot make any assumptions about the token class, i.e. whether
            # it can take a lexeme or not. Thus, no passing of lexeme here.
            txt  = "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
            txt += "RETURN;\n"
            code_fragment_list = [ CodeFragment(txt) ]

        if IndentationSupportF:
            if Mode.default_indentation_handler_sufficient():
                code = "QUEX_NAME(on_indentation)(me, /*Indentation*/0, LexemeNull);\n"
            else:
                code = "QUEX_NAME(%s_on_indentation)(me, /*Indentation*/0, LexemeNull);\n" % Mode.name

            code_fragment_list.insert(0, CodeFragment(code))

        # RETURNS: end_of_stream_action, db 
        result = __prepare(Mode, code_fragment_list,
                           None, EOF_ActionF=True, BeginOfLineSupportF=BeginOfLineSupportF)

        return PatternActionInfo(E_ActionIDs.ON_END_OF_STREAM, result)

    def do_OnFailure(self):
        if Mode.has_code_fragment_list("on_failure"):
            code_fragment_list = Mode.get_code_fragment_list("on_failure")
        else:
            txt  = "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % Mode.name 
            txt += "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
            txt += "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
            code_fragment_list = [ CodeFragment(txt) ]

        # RETURNS: on_failure_action, db 
        prepared_code = __prepare(Mode, code_fragment_list,
                                  None, Failure_ActionF=True, 
                                  BeginOfLineSupportF=BeginOfLineSupportF)

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

        return PatternActionInfo(E_ActionIDs.ON_FAILURE, CodeFragment(txt))

    def do(cls, Pattern, action):
        if hasattr(action, "data") and type(action.data) == dict:   
            action.data["indentation_counter_terminal_id"] = indentation_counter_terminal_id

    def __prepare(self, Mode, CodeFragmentList, ThePattern, Failure_ActionF=False, EOF_ActionF=False):
        """-- If there are multiple handlers for a single event they are combined
        
           -- Adding debug information printer (if desired)
        
           -- The task of this function is it to adorn the action code for each pattern with
              code for line and column number counting.
        """
        assert Mode.__class__.__name__  == "Mode"
        assert ThePattern      is None or ThePattern.__class__.__name__ == "Pattern" 
        assert type(Failure_ActionF)    == bool
        assert type(EOF_ActionF)        == bool

        code_user = self.collect_code(CodeFragmentList, Mode)

        return CodeFragment([
            self.get_code_line_column_count(ThePattern, EOF_ActionF),
            self.get_code_store_last_character(),
            self.get_code_terminating_zero(),
            self.get_code_on_match(Failure_ActionF),
            "{\n",
            code_user,
            "\n}",
        ])

    def collect_code(CodeFragmentList, Mode=None):
        global Match_Lexeme 
        LanguageDB = Setup.language_db
        IndentationBase = 1

        code_list = []
        for fragment in CodeFragmentList:
            code_list.extend(fragment.get_code(Mode))

        code_str = "".join(LanguageDB.GET_PLAIN_STRINGS(code_list))

        # If 'Lexeme' occurs as an isolated word, then ensure the generation of 
        # a terminating zero. Note, that the occurence of 'LexemeBegin' does not
        # ensure the preparation of a terminating zero.
        self.require_terminating_zero_preparation_f |= (Match_Lexeme.search(code_str) is not None) 

        return pretty_code(code_str, IndentationBase)

    def get_code_on_match(self, Failure_ActionF):
        if Failure_ActionF:
            # OnFailure == 'nothing matched'; Thus 'on_match_code' is inappropriate.
            return ""
        return self.on_match_code

    def get_code_store_last_character(self):
        if not self.begin_of_line_support_f:
            return ""

        # TODO: The character before lexeme start does not have to be written
        # into a special register. Simply, make sure that '_lexeme_start_p - 1'
        # is always in the buffer. This may include that on the first buffer
        # load '\n' needs to be at the beginning of the buffer before the
        # content is loaded. Not so easy; must be carefully approached.
        return "    %s\n" % LanguageDB.ASSIGN("me->buffer._character_before_lexeme_start", 
                                              LanguageDB.INPUT_P_DEREFERENCE(-1))

    def get_code_terminating_zero(self):
        if not self.require_terminating_zero_preparation_f:
            return ""
        return "    QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"

    def get_code_line_column_count(self, ThePattern, EOF_ActionF):
        default_counter_required_f, \
        result                      = counter_for_pattern.get(ThePattern, EOF_ActionF)
        result                      = "".join(LanguageDB.REPLACE_INDENT(lc_count_code))
        if default_counter_required_f: 
            Mode.default_character_counter_required_f_set()
        return result


def do(Mode, IndentationSupportF, BeginOfLineSupportF):
    """The module 'quex.output.cpp.core' produces the code for the 
   state machine. However, it requires a certain data format. This function
   adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    global LanguageDB
    global variable_db
    LanguageDB = Setup.language_db

    assert Mode.__class__.__name__ == "Mode"

    # -- 'on after match' action
    on_after_match, \
    require_terminating_zero_preparation_f = __prepare_on_after_match_action(Mode)

    # -- 'end of stream' action
    on_end_of_stream_action = __prepare_on_end_of_stream_action(Mode, IndentationSupportF, BeginOfLineSupportF)

    # -- 'on failure' action (on the event that nothing matched)
    on_failure_action = __prepare_on_failure_action(Mode, BeginOfLineSupportF, require_terminating_zero_preparation_f)

    # -- pattern-action pairs
    pattern_action_pair_list = Mode.get_pattern_action_pair_list()

    # Assume pattern-action pairs (matches) are sorted and their pattern state
    # machine ids reflect the sequence of pattern precedence.
    terminal_state_list = []
    for pattern_info in pattern_action_pair_list:
        action  = pattern_info.action()
        pattern = pattern_info.pattern()

        # Generated code fragments may rely on some information about the generator
        if hasattr(action, "data") and type(action.data) == dict:   
            action.data["indentation_counter_terminal_id"] = indentation_counter_terminal_id

        prepared_action = __prepare(Mode, action, pattern, \
                                    BeginOfLineSupportF=BeginOfLineSupportF, 
                                    require_terminating_zero_preparation_f=require_terminating_zero_preparation_f)

        pattern_info.set_action(prepared_action)
    
    for action in (end_of_stream_action, on_failure_action, on_after_match):
        if action is None: continue
        pattern_action_pair_list.append(action)

    return pattern_action_pair_list

def pretty_code(Code, Base):
    """-- Delete empty lines at the beginning
       -- Delete empty lines at the end
       -- Strip whitespace after last non-whitespace
       -- Propper Indendation based on Indentation Counts

       Base = Min. Indentation
    """
    class Info:
        def __init__(self, IndentationN, Content):
            self.indentation = IndentationN
            self.content     = Content
    info_list           = []
    no_real_line_yet_f  = True
    indentation_set     = set()
    for line in Code.split("\n"):
        line = line.rstrip() # Remove trailing whitespace
        if len(line) == 0 and no_real_line_yet_f: continue
        else:                                     no_real_line_yet_f = False

        content     = line.lstrip()
        if len(content) != 0 and content[0] == "#": indentation = 0
        else:                                       indentation = len(line) - len(content) + Base
        info_list.append(Info(indentation, content))
        indentation_set.add(indentation)

    # Discretize indentation levels
    indentation_list = list(indentation_set)
    indentation_list.sort()

    # Collect the result
    result              = []
    # Reverse so that trailing empty lines are deleted
    no_real_line_yet_f  = True
    for info in reversed(info_list):
        if len(info.content) == 0 and no_real_line_yet_f: continue
        else:                                             no_real_line_yet_f = False
        indentation_level = indentation_list.index(info.indentation)
        result.append("%s%s\n" % ("    " * indentation_level, info.content))

    return "".join(reversed(result))

