# (C) Frank-Rene Schaefer
from   quex.engine.analyzer.terminal.core          import Terminal
from   quex.engine.analyzer.door_id_address_label  import Label, DoorID
from   quex.engine.generator.code.core             import CodeTerminal
from   quex.engine.tools                           import typed

import quex.output.cpp.counter_for_pattern         as     counter_for_pattern

import quex.blackboard as blackboard
from   quex.blackboard import E_IncidenceIDs, setup as Setup, Lng, \
                              E_TerminalType

import re

class TerminalFactory:
    """Factory for Terminal-s
    ___________________________________________________________________________

    A TerminalStateFactory generates Terminal-s by its '.do()' member function.
    Terminal-s are created dependent on the E_TerminalTypes indicator.  The
    whole process is initiated in its constructor.
    ___________________________________________________________________________
    """
    def __init__(self, ModeName, IncidenceDb, CounterDb): 
        """Sets up the terminal factory, i.e. specifies all members required
        in the process of Terminal construction. 
        """
        self.line_column_count_db = CounterDb

        self.txt_indentation_handler_call = Lng.INDENTATION_HANDLER_CALL(
                                                  blackboard.required_support_indentation_count(), 
                                                  not IncidenceDb.default_indentation_handler(),
                                                  ModeName) 
        self.txt_default_line_column_counter_call = Lng.DEFAULT_COUNTER_CALL()
        self.txt_store_last_character = Lng.STORE_LAST_CHARACTER(blackboard.required_support_begin_of_line())

        self.on_match       = IncidenceDb.get_CodeTerminal(E_IncidenceIDs.MATCH)
        self.on_after_match = IncidenceDb.get_CodeTerminal(E_IncidenceIDs.AFTER_MATCH)

    @typed(Code=CodeTerminal)
    def do(self, TerminalType, IncidenceId, Code):
        """Construct a Terminal object based on the given TerminalType and 
        parameterize it with 'IncidenceId' and 'Code'.
        """
        return {
            E_TerminalType.MATCH_PATTERN: self.do_match_pattern,
            E_TerminalType.MATCH_FAILURE: self.do_match_failure,
            E_TerminalType.END_OF_STREAM: self.do_end_of_stream,
        }[TerminalType](IncidenceId, Code)

    def do_match_pattern(self, IncidenceId, Code):
        """A pattern has matched."""
        assert isinstance(IncidenceId, (int, long)) or IncidenceId in E_IncidenceIDs

        code_user               = pretty_code(Code.get_code())
        txt_line_column_counter = self.line_column_count_db.get(IncidenceId)

        terminating_zero_f =    self.on_match.requires_lexeme_terminating_zero_f()       \
                             or Code.requires_lexeme_terminating_zero_f()                \
                             or self.on_after_match.requires_lexeme_terminating_zero_f ()
        lexeme_begin_f     =    self.on_match.requires_lexeme_begin_f()      \
                             or Code.requires_lexeme_begin_f()               \
                             or self.on_after_match.requires_lexeme_begin_f() 

        txt_terminating_zero = Lng.LEXEME_TERMINATING_ZERO_SET(terminating_zero_f)

        assert txt_line_column_counter is not None
        code = [
            txt_line_column_counter,
            self.txt_store_last_character,
            txt_terminating_zero,
            self.on_match.get_text(),
            "{\n",
            code_user,
            "\n}\n",
            Lng.GOTO_BY_DOOR_ID(DoorID.continue_with_on_after_match())
        ] 

        name = TerminalFactory.name_pattern_match_terminal(IncidenceId, Code.pattern_string)
        return Terminal(IncidenceId, code, name, LexemeBeginRequiredF = lexeme_begin_f)

    def do_match_failure(self, IncidenceId, Code):
        """No pattern in the mode has matched. Line and column numbers are 
        still counted. But, no 'on_match' or 'on_after_match' action is 
        executed.
        """
        

        code = [ self.txt_default_line_column_counter_call ]

        code.append(Lng.IF_END_OF_FILE())
        code.append(    Lng.GOTO_BY_DOOR_ID(DoorID.continue_without_on_after_match()))
        code.append(Lng.IF_INPUT_P_EQUAL_LEXEME_START_P(FirstF=False))
        code.append(    Lng.INPUT_P_INCREMENT())
        code.append(Lng.END_IF())
        code.append("\n") 
        code.extend(Code.get_code())

        code.append(Lng.GOTO_BY_DOOR_ID(DoorID.continue_without_on_after_match()))

        return Terminal(IncidenceId, code, "FAILURE")

    def do_end_of_stream(self, IncidenceId, Code):
        """End of Stream: The terminating zero has been reached and no further
        content can be loaded.
        """
        # No indentation handler => Empty string.
        code = [ self.txt_indentation_handler_call ]
        code.extend(self.txt_default_line_column_counter_call)
        code.extend(Code.get_code())
        code.append(
            "    /* End of Stream FORCES a return from the lexical analyzer, so that no\n"
            "     * tokens can be filled after the termination token.                    */\n"
            "    RETURN;\n"
        )
        return Terminal(IncidenceId, code, "END_OF_STREAM")

    def do_plain(self, IncidenceId, Code):
        """Plain source code text as generated by quex."""
        return Terminal(IncidenceId, Code, str(IncidenceId))

    @staticmethod
    def name_pattern_match_terminal(IncidenceId, PatternString):
        def safe(Letter):
            if Letter in ['\\', '"', '\n', '\t', '\r', '\a', '\v']: return "\\" + Letter
            else:                                                   return Letter 

        safe_pattern = "".join(safe(x) for x in PatternString)
        return "%i: %s" % (IncidenceId, safe_pattern)

def pretty_code(Code, Base=4):
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
    for element in Code:
        for line in element.split("\n"):
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

