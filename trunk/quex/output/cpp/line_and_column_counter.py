# (C) 2012 Frank-Rene Schaefer
from quex.blackboard import E_Count, \
                            setup as Setup

def do(ThePattern, EOF_ActionF):
    """Prepare additional actions which are required for line and column
    number counting. 
    
    The '.newline_n' and '.column_n' of a given 'Pattern' may be given by the
    pattern itself. For example the pattern "\n\n" increments the line number
    always by 2. The pattern "\n+" however increments the line number depending
    on how many '\n' it matches at runtime. These considerations where done
    by means of 

              quex.engine.state_machine.character_counter.do(...)

    It is called inside the 'prepare_count_info()' member function of the
    pattern at the time when it is communicated to the 'Mode' object from the
    'ModeDescription' object in:

              quex.input.files.mode.Mode.__init__(...)

    As a consequence of a call to 'prepare_count_info()', the pattern's 'count'
    object must be set to something not 'None'. If it is 'None', this means
    that the 'prepare_count_info()' function has not been called for it.  
    """
    def frame(Txt):
        if len(Txt) != 0:
            Txt = "    " + Txt[:-1].replace("\n", "\n    ") + Txt[-1]
        return  "    __QUEX_COUNTER_SHIFT_VALUES(self.counter);\n" \
               + Txt                                           \
               + "   __quex_debug_counter();\n"

    LanguageDB = Setup.language_db

    if EOF_ActionF:
        return frame("")

    if ThePattern is None:
        # 'on_failure' ... count any appearing character
        return "__QUEX_COUNT_VOID(self.counter, LexemeBegin, LexemeEnd);"
        ## return "QUEX_NAME(Counter_count_with_grid)(&self.counter, LexemeBegin, LexemeEnd);\n"

    counter = ThePattern.count_info()

    # (*) If one parameter is 'VOID' than use the general counter to count.
    if    counter.line_n_increment_by_lexeme_length        == E_Count.VOID \
       or (    counter.column_n_increment_by_lexeme_length == E_Count.VOID \
           and counter.grid_step_size_by_lexeme_length     == E_Count.VOID):
        return "__QUEX_COUNT_VOID(self.counter, LexemeBegin, LexemeEnd);"

    # (*) Line Number Count
    line_txt = None

    def get_increment(Increment, IncrementByLexemeLength, HelpStr):

        if IncrementByLexemeLength == 0:
            line_txt  = ""
        elif Increment == 0:
            line_txt = ""
        else:
            if Increment != E_Count.VOID:
                arg = "%i" % Increment
            else:

                if IncrementByLexemeLength == 1: 
                    arg = "LexemeL"
                else:
                    arg = "LexemeL * %i" % IncrementByLexemeLength
            line_txt = "__QUEX_IF_COUNT_%s_ADD(%s);\n" % (HelpStr, arg)

    # Following assert results from entry check against 'VOID'
    assert counter.line_n_increment_by_lexeme_length != E_Count.VOID
    line_txt = get_increment(counter.line_n_increment, 
                             counter.line_n_increment_by_lexeme_length, 
                             "LINES")

    # (*) Column Number Count
    column_txt = None
    if counter.column_index != E_Count.VOID:
        column_txt = "__QUEX_IF_COUNT_COLUMNS_SET(%i);\n" % (counter.column_index + 1)

    if  counter.column_n_increment_by_lexeme_length != E_Count.VOID:
        column_txt = get_increment(counter.column_n_increment, 
                                   counter.column_n_increment_by_lexeme_length, 
                                   "COLUMNS")

    else:
        # Following assert results from entry check against 'VOID'
        assert counter.grid_step_size_by_lexeme_length != E_Count.VOID

        if counter.grid_step_n == E_Count.VOID: grid_step_n = "LexemeL"
        else:                                   grid_step_n = counter.grid_step_n

        column_txt = LanguageDB.GRID_STEP("self.counter._column_number_at_end", "size_t",
                                          counter.grid_step_size_by_lexeme_length, 
                                          grid_step_n)

    if line_txt is None or column_txt is None:
        return "__QUEX_COUNT_VOID(self.counter, LexemeBegin, LexemeEnd);"

    return frame(line_txt + column_txt)

