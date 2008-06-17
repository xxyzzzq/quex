import quex.core_engine.state_machine.character_counter as counter
from quex.core_engine.interval_handling import NumberSet

def do(Mode, CodeFragment_or_CodeFragments, Setup, SafePatternStr, PatternStateMachine, 
       Default_ActionF=False, EOF_ActionF=False):

    if type(CodeFragment_or_CodeFragments) == list:
        assert Default_ActionF or EOF_ActionF, \
               "Action code formatting: Multipled Code Fragments can only be specified for default or\n" + \
               "end of stream action."
        CodeFragementList = CodeFragment_or_CodeFragments
    else:
        CodeFragment = CodeFragment_or_CodeFragments

    txt = "{\n"

    # -- special code to be executed on any match
    for code_info in Mode.on_match_code_fragments():
        txt += code_info.get("C")

    # -- line number counting code
    #    (if mode requires indentation events, than a different counting scheme is used)
    if Mode.on_indentation.line_n != -1:
        txt += __get_line_and_column_counting_with_indentation(PatternStateMachine)
    elif not EOF_ActionF:
        # When there is no indentation detection involved, then there is no need to 
        # count anymore, as soon as the EOF comes in.
        txt += __get_line_and_column_counting(PatternStateMachine)

    # -- debug match display code
    if Setup.output_debug_f == True:
        txt += '#ifdef QUEX_OPTION_DEBUG_QUEX_PATTERN_MATCHES\n'
        txt += '    std::cerr << "(" << self.line_number_at_begin() << ", " << self.column_number_at_begin()'
        txt += '<< ") %s: %s \'" << Lexeme << "\'\\n";\n' % (Mode.name, SafePatternStr)
        txt += '#endif\n'
        
    # -- THE action code as specified by the user
    if not Default_ActionF and not EOF_ActionF: 
        txt += CodeFragment.get("C")
    else:                       
        if CodeFragementList != []:
            for code_info in CodeFragementList:
                txt += code_info.get("C")
        else:
            txt += "self.send(%sTERMINATION);\n" % Setup.input_token_id_prefix 
            txt += "#ifdef __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID\n"
            txt += "    return /*%sTKN_TERMINATION*/;\n" % Setup.input_token_id_prefix
            txt += "#else\n"
            txt += "    return %sTERMINATION;\n" % Setup.input_token_id_prefix
            txt += "#endif\n"

    txt += "\n}"

    return txt

def __get_line_and_column_counting_with_indentation(PatternStateMachine):

    # shift the values for line and column numbering
    txt = "self.__count_shift_end_values_to_start_values();\n"

    if PatternStateMachine == None:
        return txt + "self.count_indentation(Lexeme, LexemeL);\n"

    newline_n   = counter.get_newline_n(PatternStateMachine)
    character_n = counter.get_character_n(PatternStateMachine)

    # later implementations may consider '\t' also for indentation counting
    whitespace_set  = NumberSet(ord(' '))
    initial_triggers = PatternStateMachine.get_init_state().transitions().get_trigger_set_union()

    starts_never_on_whitespace_f = not initial_triggers.has_intersection(whitespace_set)
    contains_only_spaces_f       = counter.contains_only_spaces(PatternStateMachine)

    if newline_n != 0:
        # IDEA: (case newline_n > 0) 
        #       Try to determine number of characters backwards to newline directly
        #       from the pattern state machine.
        func = "self.count_indentation(Lexeme, LexemeL);"       

    else:
        if character_n == -1: column_increment = "LexemeL"          # based on matched lexeme
        else:                 column_increment = "%i" % character_n # fixed length
            
        if starts_never_on_whitespace_f:
            func = "self.count_indentation_NoNewline_NeverStartOnWhitespace(%s);" % column_increment
        elif contains_only_spaces_f:
            func = "self.count_indentation_NoNewline_ContainsOnlySpaces(%s);" % column_increment
        else:
            func = "self.count_indentation_NoNewline(Lexeme, LexemeL);"

    return txt + func + "\n"

def __get_line_and_column_counting(PatternStateMachine):

    if PatternStateMachine == None:
        return "__QUEX_COUNT_LINE_COLUMN_SCENARIO_GENERAL(Lexeme, LexemeL);\n"

    newline_n   = counter.get_newline_n(PatternStateMachine)
    character_n = counter.get_character_n(PatternStateMachine)

    if   newline_n == -1:
        # run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        return "__QUEX_COUNT_LINE_COLUMN_SCENARIO_GENERAL(Lexeme, LexemeL);\n"

    elif newline_n != 0:
        # TODO: Try to determine number of characters backwards to newline directly
        #       from the pattern state machine.
        return "__QUEX_COUNT_LINE_COLUMN_SCENARIO_FIXED_NEWLINE_N(Lexeme, LexemeL, %i);\n" % \
               newline_n

    else:
        if character_n == -1: incr_str = "LexemeL"
        else:                 incr_str = repr(character_n) 

        return "__QUEX_COUNT_LINE_COLUMN_SCENARIO_NO_NEWLINE_N(%s);\n" % incr_str

