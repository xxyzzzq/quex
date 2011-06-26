"""Action Preparation:

   Functions to prepare a source code fragment to be sticked into the
   lexical analyzer. This includes the following:

    -- pattern matches: 
    
       (optional) line and column counting based on the character 
       content of the lexeme. Many times, the character or line
       number count is determined by the pattern, so counting can
       be replaced by an addition of a constant (or even no count
       at all).
                            
    -- end of file/stream action:

       If not defined by the user, send 'TERMINATION' token and
       return.

    -- failure action (no match):

       If not defined by the user, abort program with a message 
       that tells that the user did not define an 'on_failure'
       handler.

(C) 2005-2011 Frank-Rene Schaefer
"""
from   quex.engine.interval_handling     import NumberSet
from   quex.engine.generator.action_info import *
from   quex.blackboard                  import setup as Setup

def do(Mode, IndentationSupportF):
    """The module 'quex.output.cpp.core' produces the code for the 
       state machine. However, it requires a certain data format. This function
       adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    assert Mode.__class__.__name__ == "Mode"
    variable_db              = {}
    # -- 'end of stream' action
    end_of_stream_action, db = __prepare_end_of_stream_action(Mode, IndentationSupportF)
    variable_db.update(db)

    # -- 'on failure' action (on the event that nothing matched)
    on_failure_action, db = __prepare_on_failure_action(Mode)
    variable_db.update(db)

    # -- pattern-action pairs
    pattern_action_pair_list        = Mode.get_pattern_action_pair_list()
    indentation_counter_terminal_id = Mode.get_indentation_counter_terminal_index()

    # Assume pattern-action pairs (matches) are sorted and their pattern state
    # machine ids reflect the sequence of pattern precedence.
    for pattern_info in pattern_action_pair_list:
        action                = pattern_info.action()
        pattern_state_machine = pattern_info.pattern_state_machine()

        # Generated code fragments may rely on some information about the generator
        if hasattr(action, "data") and type(action.data) == dict:   
            action.data["indentation_counter_terminal_id"] = indentation_counter_terminal_id

        prepared_action, db = __prepare(Mode, action, pattern_state_machine, 
                                        SelfCountingActionF=False)
        variable_db.update(db)

        pattern_info.set_action(prepared_action)
    
    return variable_db, pattern_action_pair_list, \
           PatternActionInfo(None, end_of_stream_action), \
           PatternActionInfo(None, on_failure_action)

def get_code(CodeFragmentList, variable_db={}):
    code_str = ""
    require_terminating_zero_preparation_f = False
    for code_info in CodeFragmentList:
        result = code_info.get_code()
        if type(result) == tuple: 
            result, add_variable_db = result
            variable_db.update(add_variable_db)

        if type(result) == list: code_str += "".join(result)
        else:                    code_str += result        

        if code_info.require_terminating_zero_f():
            require_terminating_zero_preparation_f = True

    return code_str, require_terminating_zero_preparation_f

def __prepare(Mode, CodeFragment_or_CodeFragments, PatternStateMachine, 
              Default_ActionF=False, EOF_ActionF=False, SelfCountingActionF=False):
    """-- If there are multiple handlers for a single event they are combined
    
       -- Adding debug information printer (if desired)
    
       -- The task of this function is it to adorn the action code for each pattern with
          code for line and column number counting.
    """
    assert Mode.__class__.__name__  == "Mode"
    assert PatternStateMachine      is None or PatternStateMachine.__class__.__name__ == "StateMachine" 
    assert type(Default_ActionF)    == bool
    assert type(EOF_ActionF)        == bool
    # We assume that any state machine presented here has been propperly created
    # and thus contains some side information about newline number, character number etc.
    assert PatternStateMachine      is None or PatternStateMachine.side_info is not None, \
           repr(PatternStateMachine)

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
        lc_count_code += "    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);\n"

    # (*) THE user defined action to be performed in case of a match
    user_code, require_terminating_zero_preparation_f = get_code(CodeFragmentList, variable_db)

    txt  = ""
    txt += on_every_match_code
    txt += "#   ifdef __QUEX_OPTION_COUNTER\n"
    txt += lc_count_code
    txt += "    __quex_debug_counter();\n"
    txt += "#   endif\n"
    txt += "    {\n"
    txt += user_code
    txt += "\n    }"

    return CodeFragment(txt, require_terminating_zero_preparation_f), variable_db

def __prepare_end_of_stream_action(Mode, IndentationSupportF):
    if not Mode.has_code_fragment_list("on_end_of_stream"):
        # We cannot make any assumptions about the token class, i.e. whether
        # it can take a lexeme or not. Thus, no passing of lexeme here.
        txt  = "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
        txt += "RETURN;\n"

        Mode.set_code_fragment_list("on_end_of_stream", CodeFragment(txt))

    if IndentationSupportF:
        if Mode.default_indentation_handler_sufficient():
            code = "QUEX_NAME(on_indentation)(me, /*Indentation*/0, LexemeNull);\n"
        else:
            code = "QUEX_NAME(%s_on_indentation)(me, /*Indentation*/0, LexemeNull);\n" % Mode.name

        code_fragment = CodeFragment(code)
        Mode.insert_code_fragment_at_front("on_end_of_stream", code_fragment)

    # RETURNS: end_of_stream_action, db 
    return __prepare(Mode, Mode.get_code_fragment_list("on_end_of_stream"), 
                     None, EOF_ActionF=True)

def __prepare_on_failure_action(Mode):
    if not Mode.has_code_fragment_list("on_failure"):
        txt  = "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % Mode.name 
        txt += "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
        txt += "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
        Mode.set_code_fragment_list("on_failure", CodeFragment(txt))

    # RETURNS: on_failure_action, db 
    return __prepare(Mode, Mode.get_code_fragment_list("on_failure"), 
                     None, Default_ActionF=True) 

def __get_line_and_column_counting(PatternStateMachine, EOF_ActionF):

    # shift the values for line and column numbering
    txt = "    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);\n" + \
          "    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);\n"

    if EOF_ActionF:
        return txt

    if PatternStateMachine is None:
        return txt + "    QUEX_NAME(Counter_count)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);\n"

    newline_n   = PatternStateMachine.side_info.get_newline_n()
    character_n = PatternStateMachine.side_info.get_character_n()

    if   newline_n == -1:
        # Run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        return txt + "    QUEX_NAME(Counter_count)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);\n"

    elif newline_n != 0:
        txt += "    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_end += %i);\n" % newline_n 
        if PatternStateMachine.get_ending_character_set().contains_only(ord('\n')):
            # A pattern that ends with newline, lets the next column start at zero.
            txt += "    __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n"
        else:
            # TODO: Try to determine number of characters backwards to newline directly
            #       from the pattern state machine. (Those seldom cases won't bring much
            #       speed-up)
            txt += "    QUEX_NAME(Counter_count_chars_to_newline_backwards)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);\n"
        return txt

    else:
        if character_n == -1: incr_str = "    ((size_t)(self.buffer._input_p - self.buffer._lexeme_start_p))"
        else:                 incr_str = "%i" % int(character_n)

        return txt + "    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += %s);\n" % incr_str

