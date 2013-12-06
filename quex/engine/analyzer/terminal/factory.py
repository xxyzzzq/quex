# (C) Frank-Rene Schaefer
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
    """Factory for Terminal-s
    ___________________________________________________________________________

    A TerminalStateFactory generates Terminal-s by its '.do()' member function.
    Terminal-s are created dependent on the E_TerminalTypes indicator.  The
    whole process is initiated in its constructor.
    ___________________________________________________________________________
    """
    def __init__(self, ModeName, IncidenceDb, CounterDb, 
                 IndentationSupportF, BeginOfLineSupportF):
        """Sets up the terminal factory, i.e. specifies all members required
        in the process of Terminal construction. 
        """
        self.txt_indentation_handler_call = LanguageDB.INDENTATION_HANDLER_CALL(
                                                  IndentationSupportF, 
                                                  not IncidenceDb.default_indentation_handler(),
                                                  ModeName) 
        self.txt_default_line_column_counter_call = LanguageDB.DEFAULT_COUNTER_CALL(ModeName)
        self.txt_store_last_character = LanguageDB.STORE_LAST_CHARACTER(BeginOfLineSupportF)

        self.txt_on_match       = IncidenceDb.get_text(E_IncidenceIDs.MATCH)
        self.txt_on_after_match = IncidenceDb.get_text(E_IncidenceIDs.AFTER_MATCH)

    def do(self, TerminalType, IncidenceId, Code, Prefix):
        """Construct a Terminal object based on the given TerminalType and 
        parameterize it with 'IncidenceId' and 'Code'.
        """
        return {
            E_TerminalTypes.MATCH_PATTERN: self.do_match_pattern,
            E_TerminalTypes.MATCH_FAILURE: self.do_match_failure,
            E_TerminalTypes.END_OF_STREAM: self.do_end_of_stream,
            E_TerminalTypes.PLAIN:         self.do_plain,
        }[TerminalType](IncidenceId, Code)

    def do_match_pattern(self, IncidenceId, Code):
        """A pattern has matched."""
        assert isinstance(IncidenceId, (int, long)) or IncidenceId in E_IncidenceIDs
        assert isinstance(Code, CodeFragment) or Code is None

        code_user                  = pretty_code(Code.get_code())
        txt_line_column_counter    = self.line_column_count_db.get(IncidenceId)

        require_terminating_zero_f =   self.on_match.lexeme_terminating_zero_required_f \
                                     | Code.lexeme_terminating_zero_required_f  
                                     | self.on_after_match.lexeme_terminating_zero_required_f \
        require_lexeme_begin_f     =   self.on_match.lexeme_begin_required_f \
                                     | Code.lexeme_begin_required_f 
                                     | self.on_after_match.lexeme_begin_required_f \

        txt_terminating_zero       = LanguageDB.LEXEME_TERMINATING_ZERO_SET(require_terminating_zero_f)

        assert code_line_column_counter is not None
        code = [
            txt_line_column_counter,
            self.txt_store_last_character,
            txt_terminating_zero,
            self.txt_on_match,
            "{\n",
            code_user,
            "\n}"
        ] 

        return Terminal(IncidenceId, code, LexemeBeginRequiredF = require_lexeme_begin_f)

    def do_match_failure(self, IncidenceId, Code):
        """No pattern in the mode has matched. Line and column numbers are 
        still counted. But, no 'on_match' or 'on_after_match' action is 
        executed.
        """
        LanguageDB = Setup.language_db

        code = self.txt_default_line_column_counter_call

        code.append(LanguageDB.IF_END_OF_FILE())
        code.append(    LanguageDB.GOTO_BY_DOOR_ID(DoorID.global_reentry_preparation_2())
        code.append(LanguageDB.IF_INPUT_P_EQUAL_LEXEME_START_P(FirstF=False))
        code.append(    LanguageDB.INPUT_P_INCREMENT())
        code.append(LanguageDB.END_IF())
    
        code.extend(Code.get_code())

        code.append(LanguageDB.GOTO_BY_DOOR_ID(DoorID.global_reentry_preparation_2())

        return Terminal(IncidenceId, code)

    def do_end_of_stream(self, IncidenceId, Code):
        """End of Stream: The terminating zero has been reached and no further
        content can be loaded.
        """
        # No indentation handler => Empty string.
        code = [ self.txt_indentation_handler_call ]
        code.extend(self.txt_default_line_column_counter_call)
        code.extend(Code)

        return Terminal(IncidenceId, code)

    def do_plain(self, IncidenceId, Code):
        """Plain source code text as generated by quex."""
        return Terminal(IncidenceId, Code)

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

