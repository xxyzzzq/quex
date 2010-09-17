import quex.core_engine.state_machine.character_counter as pattern_analyzer
from   quex.core_engine.interval_handling     import NumberSet
from   quex.core_engine.generator.action_info import *
from   quex.input.setup                       import setup as Setup

def do(Mode, CodeFragment_or_CodeFragments, SafePatternStr, PatternStateMachine, 
       Default_ActionF=False, EOF_ActionF=False, SelfCountingActionF=False):
    """-- If there are multiple handlers for a single event they are combined
    
       -- Adding debug information printer (if desired)
    
       -- The task of this function is it to adorn the action code for each pattern with
          code for line and column number counting.
    """
    assert Mode.__class__.__name__                == "Mode"
    assert type(SafePatternStr)                   == str
    assert PatternStateMachine.__class__.__name__ == "StateMachine" or PatternStateMachine == None
    assert type(Default_ActionF)                  == bool
    assert type(EOF_ActionF)                      == bool

    if type(CodeFragment_or_CodeFragments) == list:
        assert Default_ActionF or EOF_ActionF, \
               "Action code formatting: Multiple Code Fragments can only be specified for default or\n" + \
               "end of stream action."
        CodeFragmentList = CodeFragment_or_CodeFragments
    else:
        CodeFragmentList = [ CodeFragment_or_CodeFragments ]

    on_every_match_code = ""
    lc_count_code       = ""
    debug_code          = ""
    user_code           = ""
    variable_db         = {}

    # (*) Code to be performed on every match -- before the related action
    for code_info in Mode.get_code_fragment_list("on_match"):
        on_every_match_code += code_info.get_code()

    # (*) Code to count line and column numbers
    if not SelfCountingActionF: 
        lc_count_code  = __get_line_and_column_counting(PatternStateMachine, EOF_ActionF)

    if (not Default_ActionF) and (not EOF_ActionF):
        lc_count_code += "__QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);\n"

    # (*) debug prints -- if desired
    if Setup.output_debug_f == True:
        txt  = '#ifdef QUEX_OPTION_DEBUG_QUEX_PATTERN_MATCHES\n'
        txt += '    std::cerr << "(" << self.line_number_at_begin() << ", " << self.column_number_at_begin()'
        txt += '<< ") %s: %s \'" << Lexeme << "\'\\n";\n' % (Mode.name, SafePatternStr)
        txt += '#endif\n'
        debug_code = txt
        
    # (*) THE user defined action to be performed in case of a match
    require_terminating_zero_preparation_f = False
    for code_info in CodeFragmentList:
        result = code_info.get_code()
        if type(result) != tuple: 
            user_code += result
        else:
            user_code += result[0]
            variable_db.update(result[1])
        if code_info.require_terminating_zero_f():
            require_terminating_zero_preparation_f = True

    txt  = "{\n"
    txt += on_every_match_code
    txt += "#   ifdef __QUEX_OPTION_COUNTER\n"
    txt += lc_count_code
    txt += "#   endif\n"
    txt += debug_code
    txt += user_code
    txt += "\n}"

    return CodeFragment(txt, require_terminating_zero_preparation_f), variable_db

def __get_line_and_column_counting(PatternStateMachine, EOF_ActionF):

    # shift the values for line and column numbering
    txt = "__QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);\n" + \
          "__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);\n"

    if EOF_ActionF:
        return txt

    if PatternStateMachine == None:
        return txt + "QUEX_NAME(Counter_count)(&self.counter, Lexeme, LexemeEnd);\n"

    newline_n   = pattern_analyzer.get_newline_n(PatternStateMachine)
    character_n = pattern_analyzer.get_character_n(PatternStateMachine)

    if   newline_n == -1:
        # Run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        return txt + "QUEX_NAME(Counter_count)(&self.counter, Lexeme, LexemeEnd);\n"

    elif newline_n != 0:
        txt += "__QUEX_IF_COUNT_LINES(self.counter._line_number_at_end += %i);\n" % newline_n 
        if PatternStateMachine.get_ending_character_set().contains_only(ord('\n')):
            # A pattern that ends with newline, lets the next column start at zero.
            txt += "__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n"
        else:
            # TODO: Try to determine number of characters backwards to newline directly
            #       from the pattern state machine. (Those seldom cases won't bring much
            #       speed-up)
            txt += "QUEX_NAME(Counter_count_chars_to_newline_backwards)(&self.counter, Lexeme, LexemeEnd);\n"
        return txt

    else:
        if character_n == -1: incr_str = "LexemeL"
        else:                 incr_str = "%i" % int(character_n)

        return txt + "__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += %s);\n" % incr_str

