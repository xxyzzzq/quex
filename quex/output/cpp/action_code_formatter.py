import quex.core_engine.state_machine.character_counter as counter
from quex.core_engine.interval_handling import NumberSet

def do(Mode, CodeFragment, Setup, SafePatternStr, PatternStateMachine):
    txt = "{"
    txt += "\n"

    for code_info in Mode.on_match_code_fragments():
        txt += code_info.get("C")

    if Mode.on_indentation.line_n != -1:
        txt += __get_line_and_column_counting_with_indentation(PatternStateMachine)
    else:
        txt += __get_line_and_column_counting(PatternStateMachine)

    if Setup.output_debug_f == True:
        txt += '#ifdef QUEX_OPTION_DEBUG_QUEX_PATTERN_MATCHES\n'
        txt += '    std::cerr << "(" << self.line_number_at_begin() << ", " << self.column_number_at_begin()'
        txt += '<< ") %s: %s \'" << Lexeme << "\'\\n";\n' % (Mode.name, SafePatternStr)
        txt += '#endif\n'
        
    txt += CodeFragment.get("C") + "\n}"

    return txt

def __get_line_and_column_counting_with_indentation(PatternStateMachine):

    # shift the values for line and column numbering
    txt  = "self.__count_shift_end_values_to_start_values();\n"

    if PatternStateMachine == None:
        return txt + "self.count_indentation(Lexeme, LexemeL);\n"

    newline_n   = counter.get_newline_n(PatternStateMachine)
    character_n = counter.get_character_n(PatternStateMachine)

    # later implementations may consider '\t' also for indentation counting
    whitespace_set  = NumberSet(ord(' '))
    initial_triggers = PatternStateMachine.get_init_state().get_trigger_set_union()

    starts_never_on_whitespace_f = initial_triggers.intersection(whitespace_set).is_empty()
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

    txt  = "self.__count_shift_end_values_to_start_values();\n"
    if PatternStateMachine == None:
        return txt + "self.count(Lexeme, LexemeL);\n"

    newline_n   = counter.get_newline_n(PatternStateMachine)
    character_n = counter.get_character_n(PatternStateMachine)

    if   newline_n == -1:
        # run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        func = "self.count(Lexeme, LexemeL);"       

    elif newline_n != 0:
        # IDEA: Try to determine number of characters backwards to newline directly
        #       from the pattern state machine.
        func = "self.count_FixedNewlineN(Lexeme, LexemeL, %i);" % newline_n

    else:
        if character_n == -1: func = "self.count_NoNewline(LexemeL);"
        else:                 func = "self.count_NoNewline(%i);" % character_n
            
    return txt + func + "\n"

