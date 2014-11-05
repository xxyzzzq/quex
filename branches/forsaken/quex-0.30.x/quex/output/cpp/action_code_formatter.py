import quex.core_engine.state_machine.character_counter as pattern_analyzer
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

    if Mode.on_indentation.line_n != -1:
        # (*) counters for possible count of lines, columns and indentation
        txt += __get_line_and_column_counting_with_indentation(PatternStateMachine, EOF_ActionF)

    else:
        # (*) counter to possibly count lines and colums (but no indentation)
        txt += __get_line_and_column_counting(PatternStateMachine, EOF_ActionF)

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

def __get_line_and_column_counting_with_indentation(PatternStateMachine, EOF_ActionF):

    # shift the values for line and column numbering
    txt = "self.counter.__shift_end_values_to_start_values();\n"

    if EOF_ActionF:
        txt += "#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT\n"
        txt += "    self.counter.on_end_of_file();\n"
        txt += "#endif\n"
        return txt

    if PatternStateMachine == None:
        return txt + "self.counter.icount(Lexeme, LexemeEnd);\n"

    newline_n   = pattern_analyzer.get_newline_n(PatternStateMachine)
    character_n = pattern_analyzer.get_character_n(PatternStateMachine)

    # later implementations may consider '\t' also for indentation counting
    whitespace_set  = NumberSet(ord(' '))
    initial_triggers = PatternStateMachine.get_init_state().transitions().get_trigger_set_union()

    starts_never_on_whitespace_f = not initial_triggers.has_intersection(whitespace_set)
    contains_only_spaces_f       = pattern_analyzer.contains_only_spaces(PatternStateMachine)

    if newline_n != 0:
        # IDEA: (case newline_n > 0) 
        #       Try to determine number of characters backwards to newline directly
        #       from the pattern state machine.
        func = "self.counter.icount(Lexeme, LexemeEnd);"       

    else:
        if character_n == -1: column_increment = "LexemeL"          # based on matched lexeme
        else:                 column_increment = "%i" % character_n # fixed length
            
        if starts_never_on_whitespace_f:
            func = "self.counter.icount_NoNewline_NeverStartOnWhitespace(%s);" % column_increment
        elif contains_only_spaces_f:
            func = "self.counter.icount_NoNewline_ContainsOnlySpaces(%s);" % column_increment
        else:
            func = "self.counter.icount_NoNewline(Lexeme, LexemeEnd);"

    return txt + func + "\n"

def __get_line_and_column_counting(PatternStateMachine, EOF_ActionF):

    # shift the values for line and column numbering
    txt = "self.counter.__shift_end_values_to_start_values();\n"

    if EOF_ActionF:
        return txt

    if PatternStateMachine == None:
        return txt + "self.counter.count(Lexeme, LexemeEnd);\n"

    newline_n   = pattern_analyzer.get_newline_n(PatternStateMachine)
    character_n = pattern_analyzer.get_character_n(PatternStateMachine)

    if   newline_n == -1:
        # run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        return txt + "self.counter.count(Lexeme, LexemeEnd);\n"

    elif newline_n != 0:
        # TODO: Try to determine number of characters backwards to newline directly
        #       from the pattern state machine. (Those seldom cases won't bring much
        #       speed-up)
        return txt + "self.counter.count_FixNewlineN(Lexeme, LexemeEnd, %i);\n" % newline_n

    else:
        if character_n == -1: incr_str = "LexemeL"
        else:                 incr_str = repr(character_n) 

        return txt + "self.counter.count_NoNewline(%s);\n" % incr_str

