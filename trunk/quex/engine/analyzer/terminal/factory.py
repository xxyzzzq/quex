# (C) Frank-Rene Schaefer
from   quex.input.regular_expression.construct     import Pattern
from   quex.engine.analyzer.terminal.core          import Terminal, TerminalGenerated
from   quex.engine.analyzer.door_id_address_label  import DoorID
from   quex.input.code.core                        import CodeTerminal
from   quex.engine.misc.tools                      import typed
from   quex.engine.misc.string_handling            import safe_string

import quex.output.cpp.counter_for_pattern         as     counter_for_pattern

import quex.blackboard as blackboard
from   quex.blackboard import Lng, \
                              E_IncidenceIDs, \
                              E_TerminalType

import types

class TerminalFactory:
    """Factory for Terminal-s
    ___________________________________________________________________________

    A TerminalStateFactory generates Terminal-s by its '.do()' member function.
    Terminal-s are created dependent on the E_TerminalTypes indicator.  The
    whole process is initiated in its constructor.

    Additionally, the factory keeps track of the necessity to count lexemes
    and the necessity of a default counter for line and column number.
    ___________________________________________________________________________
    """
    def __init__(self, ModeName, IncidenceDb): 
        """Sets up the terminal factory, i.e. specifies all members required
        in the process of Terminal construction. 
        """
        self.required_default_counter_f   = False

        if blackboard.required_support_indentation_count(): 
            self.txt_indentation_handler_call = Lng.INDENTATION_HANDLER_CALL(
                                                    IncidenceDb.default_indentation_handler_f(),
                                                    ModeName) 
        else:
            self.txt_indentation_handler_call = ""

        self.txt_store_last_character = Lng.STORE_LAST_CHARACTER(blackboard.required_support_begin_of_line())

        self.on_match       = IncidenceDb.get_CodeTerminal(E_IncidenceIDs.MATCH)
        self.on_after_match = IncidenceDb.get_CodeTerminal(E_IncidenceIDs.AFTER_MATCH)

    @typed(Code=CodeTerminal)
    def do(self, TerminalType, Code, ThePattern=None):
        """Construct a Terminal object based on the given TerminalType and 
        parameterize it with 'IncidenceId' and 'Code'.
        """
        if ThePattern is not None:
            assert ThePattern.count_info() is not None

        return {
            E_TerminalType.MATCH_PATTERN: self.do_match_pattern,
            E_TerminalType.MATCH_FAILURE: self.do_match_failure,
            E_TerminalType.END_OF_STREAM: self.do_end_of_stream,
            E_TerminalType.BAD_LEXATOM:   self.do_bad_lexatom,    # Treated as 'end_of_stream'
            E_TerminalType.LOAD_FAILURE:  self.do_load_failure,   # Treated as 'end_of_stream'
            E_TerminalType.OVERFLOW:      self.do_overflow,       # Treated as 'end_of_stream'
            E_TerminalType.PLAIN:         self.do_plain,
        }[TerminalType](Code, ThePattern)

    @typed(ThePattern=Pattern)
    def do_match_pattern(self, Code, ThePattern):
        """A pattern has matched."""

        lexeme_begin_f,     \
        terminating_zero_f, \
        adorned_code        = self.__adorn_user_code(Code, MatchF=True)

        # IMPORTANT: Terminals can be entered by any kind of 'GOTO'. In order to
        #            be on the safe side, BIPD should be started from within the
        #            terminal itself. Otherwise, it may be missed due to some 
        #            coding negligence.
        text = []
        if ThePattern.bipd_sm is not None:
            TerminalFactory.do_bipd_entry_and_return(text, ThePattern)

        text.extend([
            self.__counter_code(ThePattern),
            #
            adorned_code,
            #
            Lng.GOTO(DoorID.continue_with_on_after_match())
        ])
        return self.__terminal(text, Code, 
                               safe_string(ThePattern.pattern_string()),
                               LexemeRelevanceF       = True,
                               LexemeBeginF           = lexeme_begin_f,
                               LexemeTerminatingZeroF = terminating_zero_f)

    def do_match_failure(self, Code, ThePattern):
        """No pattern in the mode has matched. Line and column numbers are 
        still counted. But, no 'on_match' or 'on_after_match' action is 
        executed.
        """
        lexeme_begin_f,     \
        terminating_zero_f, \
        adorned_code        = self.__adorn_user_code(Code, MatchF=False)

        text = [ 
            #Lng.IF_END_OF_FILE(),
            #    self.__counter_code(None),
            #    Lng.GOTO(DoorID.continue_without_on_after_match()),
            #Lng.IF_INPUT_P_EQUAL_LEXEME_START_P(FirstF=False),
            #    Lng.INPUT_P_INCREMENT(),
            #Lng.END_IF(),
            self.__counter_code(None),
            #
            adorned_code,
            #
            Lng.GOTO(DoorID.continue_without_on_after_match()),
        ]
        return self.__terminal(text, Code, "FAILURE")

    def do_end_of_stream(self, Code, ThePattern):
        """End of Stream: The terminating zero has been reached and no further
        content can be loaded.
        """
        comment_txt = "End of Stream FORCES a return from the lexical analyzer, so that no\n" \
                      "tokens can be filled after the termination token."
        return self.__terminate_analysis_step(Code, "END_OF_STREAM", comment_txt)

    def do_bad_lexatom(self, Code, ThePattern):
        """Bad lexatom: an input appeared beyond the addmissible alphabet or the
        an inadmissible sequence has been detected (e.g. in UTF8).

        As with temination: the TERMINATION token is sent, if not defined differently.
        """
        comment_txt = "Bad lexatom detection FORCES a return from the lexical analyzer, so that no\n" \
                      "tokens can be filled after the termination token."
        return self.__terminate_analysis_step(Code, "BAD_LEXATOM", comment_txt)

    def do_load_failure(self, Code, ThePattern):
        """Load failure: loading of buffer failed due to an unspecific reason.
        The reason could not be determined inside the Quex framework.

        As with temination: the TERMINATION token is sent, if not defined differently.
        """
        comment_txt = "Load failure FORCES a return from the lexical analyzer, so that no\n" \
                      "tokens can be filled after the termination token."
        return self.__terminate_analysis_step(Code, "LOAD_FAILURE", comment_txt)

    def do_overflow(self, Code, ThePattern):
        """Overflow: Lexeme size exceeds buffer size.

        As with temination: the TERMINATION token is sent, if not defined differently.
        """
        comment_txt = "Lexeme size exceeds buffer size. No further buffer load possible."
        return self.__terminate_analysis_step(Code, "OVERFLOW", comment_txt)

    def do_plain(self, Code, ThePattern):
        """Plain source code text as generated by quex."""

        text = [
            self.__counter_code(ThePattern)
        ]
        text.extend(
            Code.get_code()
        )

        if ThePattern is None: name = "<no name>"
        else:                  name = ThePattern.pattern_string()

        return self.__terminal(text, Code, name)

    @typed(ThePattern=(None, Pattern), GeneratorFunction=types.FunctionType, Data=dict, Name=(str,unicode))
    def do_generator(self, ThePattern, GeneratorFunction, Data, Name):
        if ThePattern is not None:
            prefix_code = [ self.__counter_code(ThePattern) ]
        else:
            prefix_code = []
        return TerminalGenerated(GeneratorFunction, Data, Name, prefix_code) 

    def __lexeme_flags(self, Code):
        lexeme_begin_f     =    self.on_match.requires_lexeme_begin_f()      \
                             or Code.requires_lexeme_begin_f()               \
                             or self.on_after_match.requires_lexeme_begin_f() 
        terminating_zero_f =    self.on_match.requires_lexeme_terminating_zero_f()       \
                             or Code.requires_lexeme_terminating_zero_f()                \
                             or self.on_after_match.requires_lexeme_terminating_zero_f ()
        return lexeme_begin_f, terminating_zero_f

    @staticmethod
    def do_bipd_entry_and_return(txt, ThePattern):
        """(This is a very seldom case) After the pattern has matched, one needs 
        to determine the end of the lexeme by 'backward input position detection' 
        (bipd). Thus,

              TERMINAL 
                   '----------.
                       (goto) '---------> BIPD State Machine
                                               ...
                                          (determine _read_p)
                                               |
                      (label) .----------------'
                   .----------'
                   |
              The actions on 
              pattern match.
        """
        door_id_entry  = DoorID.state_machine_entry(ThePattern.bipd_sm.get_id())
        door_id_return = DoorID.bipd_return(ThePattern.incidence_id())
        txt.append("    %s\n%s\n" 
           % (Lng.GOTO(door_id_entry),   # Enter BIPD
              Lng.LABEL(door_id_return)) # Return from BIPD
        )

    def __counter_code(self, ThePattern):
        """Get the text of the source code required for 'counting'. This information
        has been stored along with the pattern before any transformation happened.
        No database or anything is required as this point.
        """
        default_counter_f, \
        text               = counter_for_pattern.get(ThePattern)

        self.required_default_counter_f |= default_counter_f
        return "".join(Lng.REPLACE_INDENT(text))

    def __adorn_user_code(self, Code, MatchF):
        """Adorns user code with:
           -- storage of last character, if required for 'begin of line'
              pre-context.
           -- storage of the terminating zero, if the lexeme is required
              as a zero-terminated string.
           -- add the 'on_match' event handler in front, if match is relevant.
           -- adding source reference information.
        """
        code_user = Lng.SOURCE_REFERENCED(Code)

        lexeme_begin_f, \
        terminating_zero_f = self.__lexeme_flags(Code)

        txt_terminating_zero = Lng.LEXEME_TERMINATING_ZERO_SET(terminating_zero_f)

        if MatchF: txt_on_match = Lng.SOURCE_REFERENCED(self.on_match)
        else:      txt_on_match = ""

        result = "".join([
            self.txt_store_last_character,
            txt_terminating_zero,
            txt_on_match,
            "{\n",
            code_user,
            "\n}\n",
        ])

        return lexeme_begin_f, terminating_zero_f, result

    def __terminate_analysis_step(self, Code, Name, Comment):
        lexeme_begin_f,     \
        terminating_zero_f, \
        adorned_code        = self.__adorn_user_code(Code, MatchF=True)
        
        # No indentation handler => Empty string.
        text = [ 
            Lng.DEFAULT_COUNTER_CALL(),
            self.txt_indentation_handler_call,
            #
            adorned_code,
            #
            Lng.ML_COMMENT(Comment),
            Lng.GOTO(DoorID.return_with_on_after_match()),
        ]
        return self.__terminal(text, Code, Name)

    def __terminal(self, Text, Code, Name,
                   LexemeRelevanceF=bool, LexemeTerminatingZeroF=bool, LexemeBeginF=bool):
        code = CodeTerminal(Text, SourceReference = Code.sr, 
                            PureCode = Code.get_pure_code())
        return Terminal(code, Name)

