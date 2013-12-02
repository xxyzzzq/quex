from   quex.engine.analyzer.terminal.core                import TerminalPlainCode
from   quex.engine.analyzer.terminal.skip                import TerminalSkipCharacterSet
from   quex.engine.analyzer.terminal.skip_range          import TerminalSkipRange
from   quex.engine.analyzer.terminal.skip_nested_range   import TerminalSkipNestedRange
from   quex.engine.analyzer.terminal.indentation_handler import TerminalIndentationHandler
from   quex.engine.analyzer.door_id_address_label        import Label, DoorID
from   quex.engine.generator.code.core                   import CodeFragment

import quex.output.cpp.counter_for_pattern         as     counter_for_pattern

from   quex.blackboard import E_IncidenceIDs, setup as Setup

import re

Match_Lexeme                = re.compile("\\bLexeme\\b", re.UNICODE)
Match_Lexeme_or_LexemeBegin = re.compile("\\bLexeme\\b|\\bLexemeBegin\\b", re.UNICODE)

class TerminalStateFactory:
    def __init__(self, ModeName, IncidenceDb, CounterDb, CounterDefaultF, 
                 IndentationSupportF, BeginOfLineSupportF):

        self.line_column_count_db = CounterDb
        self.default_counter_f    = CounterDefaultF

        self.incidence_db = IncidenceDb

        self.txt_indentation_handler_call = self.get_indentation_handler_call(ModeName, IndentationSupportF, 
                                                                              IncidenceDb)

        self.code_store_last_character          = self.get_code_store_last_character(BeginOfLineSupportF)

        self.code_on_match = IncidenceDb.,          \
        self.rtz_on_match_f,         \
        self.lexeme_on_match_f       = self.collect_code(IncidenceDb.get(E_IncidenceIDs.MATCH)) 
        self.code_on_after_match,    \
        self.rtz_on_after_match_f,   \
        self.lexeme_on_after_match_f = self.collect_code(IncidenceDb.get(E_IncidenceIDs.AFTER_MATCH))

        self.mode_name = ModeName

    def do_OnEndOfStream(self):
        # No indentation handler => Empty string.
        code = [ self.txt_indentation_handler_call ]

        if self.incidence_db.has_key(E_IncidenceIDs.END_OF_STREAM):
            code.extend(self.incidence_db[E_IncidenceIDs.END_OF_STREAM].get_code())
        else:
            # We cannot make any assumptions about the token class, i.e. whether
            # it can take a lexeme or not. Thus, no passing of lexeme here.
            code.append(
                "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
                "RETURN;\n"
            )

        code_fragment = self.prepare_CodeFragment(E_IncidenceIDs.END_OF_STREAM, code)

        return TerminalPlainCode(E_IncidenceIDs.END_OF_STREAM, code_fragment)

    def do_OnFailure(self):
        LanguageDB = Setup.language_db

        if self.incidence_db.has_key(E_IncidenceIDs.FAILURE):
            code_fragment = self.incidence_db[E_IncidenceIDs.FAILURE]
        else:
            txt  = "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % self.mode_name 
            txt += "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
            txt += "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
            code_fragment = CodeFragment(txt) 

        prepared_code = self.prepare_CodeFragment(E_IncidenceIDs.FAILURE, code_fragment) 

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
            1,     "%s\n" % prepared_code.get_code_string(), 
            1,     "%s\n" % LanguageDB.GOTO_BY_DOOR_ID(DoorID.global_reentry_preparation_2())
        ]

        return TerminalPlainCode(E_IncidenceIDs.FAILURE, CodeFragment(txt))

    def prepare_CodeFragment(self, IncidenceId, TheCodeFragment):
        """-- If there are multiple handlers for a single event they are combined
        
           -- Adding debug information printer (if desired)
        
           -- The task of this function is it to adorn the action code for each pattern with
              code for line and column number counting.
        """
        assert isinstance(IncidenceId, (int, long)) or IncidenceId in E_IncidenceIDs
        assert isinstance(TheCodeFragment, CodeFragment) or TheCodeFragment is None

        if TheCodeFragment.subject_to_match_f():
            code_on_match = self.get_code_on_match(IncidenceId)
        else:
            code_on_match = UserCode_Empty

        code_user                = self.collect_code(TheCodeFragment)
        code_line_column_counter = self.line_column_count_db.get(IncidenceId)
        if code_line_column_counter is None: code_line_column_counter  = ""
        code_store_last_character     = self.code_store_last_character

        require_terminating_zero_f    =   self.on_after_match.lexeme_terminating_zero_required_f \
                                        | code_on_match.lexeme_terminating_zero_required_f \
                                        | code_user.lexeme_terminating_zero_required_f  
        require_lexeme_begin_f        =   self.on_after_match.lexeme_begin_required_f \
                                        | code_on_match.lexeme_begin_required_f \
                                        | code_user.lexeme_begin_required_f 

        code_terminating_zero         = self.get_code_terminating_zero(require_terminating_zero_f)

        code = [
            code_line_column_counter,
            code_store_last_character,
            code_terminating_zero,
            code_on_match,
            "{\n",
            code_user,
            "\n}"
        ] 

        return CodeFinalized(code, 
                             LexemeTerminatingZeroRequiredF = require_terminating_zero_f, 
                             LexemeBeginRequiredF = require_lexeme_begin_f)

    def collect_code(self, TheCodeFragment):
        """RETURNS:  
           [0] -- The code contained in 'TheCodeFragment' as string. The 
                  string is 'pretty printed'.
           [1] -- True, if a terminating zero for the lexeme is required.
                  False, if not.
        """
        if TheCodeFragment is None:
            return "", False

        assert isinstance(TheCodeFragment, CodeFragment)
        global Match_Lexeme 
        LanguageDB = Setup.language_db

        code_str = "".join(LanguageDB.GET_PLAIN_STRINGS(TheCodeFragment.get_code(Mode=None)))

        # If 'Lexeme' occurs as an isolated word, then ensure the generation of 
        # a terminating zero. Note, that the occurence of 'LexemeBegin' does not
        # ensure the preparation of a terminating zero.
        require_terminating_zero_preparation_f = (Match_Lexeme.search(code_str) is not None) 
        require_lexeme_begin_f                 = require_terminating_zero_preparation_f \
                                                 or (Match_LexemeBegin.search(code_str) is not None) 

        return pretty_code(code_str, Base=0), \
               require_terminating_zero_preparation_f, \
               require_lexeme_begin_f

    def get_code_on_match(self, IncidenceId):
        if IncidenceId == E_IncidenceIDs.FAILURE: # OnFailure == 'nothing matched'; 
            return "", False                      # => 'on_match_code' is inappropriate.
        return self.code_on_match, self.rtz_on_match_f, self.lexeme_on_match_f

    def get_code_terminating_zero(self, RequireTerminatingZeroF):
        if not RequireTerminatingZeroF:
            return ""
        return "    QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"

    def get_indentation_handler_call(self, ModeName, IndentationSupportF, IncidenceDb):
        if   not IndentationSupportF:                              return ""
        elif IncidenceDb.dedicated_indentation_handler_required(): prefix = ""
        else:                                                      prefix = ModeName + "_" 
        
        return "    QUEX_NAME(%son_indentation)(me, /*Indentation*/0, LexemeNull);\n" % prefix

    def get_code_store_last_character(self, BeginOfLineSupportF):
        LanguageDB = Setup.language_db
        if not BeginOfLineSupportF:
            return ""
        # TODO: The character before lexeme start does not have to be written
        # into a special register. Simply, make sure that '_lexeme_start_p - 1'
        # is always in the buffer. This may include that on the first buffer
        # load '\n' needs to be at the beginning of the buffer before the
        # content is loaded. Not so easy; must be carefully approached.
        return "    %s\n" % LanguageDB.ASSIGN("me->buffer._character_before_lexeme_start", 
                                              LanguageDB.INPUT_P_DEREFERENCE(-1))

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

