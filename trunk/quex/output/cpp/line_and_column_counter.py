# (C) 2012 Frank-Rene Schaefer
from quex.blackboard import E_Count

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
    return __do(ThePattern, EOF_ActionF) \
           + "    __quex_debug_counter();\n"

def __do(ThePattern, EOF_ActionF):

    if EOF_ActionF:
        return "__QUEX_COUNTER_SHIFT_VALUES(self.counter);\n" 

    if ThePattern is None:
        # 'on_failure' ... count any appearing character
        return "QUEX_NAME(Counter_count)(&self.counter, LexemeBegin, LexemeEnd);\n"
        ## return "QUEX_NAME(Counter_count_with_grid)(&self.counter, LexemeBegin, LexemeEnd);\n"

    counter = ThePattern.count_info()

    if not counter.is_partly_determined():
        return "QUEX_NAME(Counter_count)(&self.counter, LexemeBegin, LexemeEnd);\n"

    # (*) Column Number Increment Considerations
    if counter.grid != E_Count.VOID:
        assert counter.column_n_increment                  == E_Count.VOID
        assert counter.column_n_increment_by_lexeme_length == E_Count.VOID
        if counter.grid == 1: arg = None
        else:                 arg = counter.grid
        core_txt = LanguageDB.GRID_STEP("self.counter._column_number_at_end", 
                                        counter.grid_width, arg)
        column_txt = "__QUEX_IF_COUNT_COLUMNS(%s);\n" % core_txt

    elif counter.column_n_increment != E_Count.VOID:
        column_txt = "__QUEX_IF_COUNT_COLUMNS_ADD(%s);\n" % counter.column_n_increment

    elif counter.column_n_increment_by_lexeme_length != E_Count.VOID:
        x = counter.column_n_increment_by_lexeme_length
        if x == 1: arg = "LexemeL"
        else:      arg = "LexemeL * %i" % x
        column_txt = "__QUEX_IF_COUNT_COLUMNS_ADD(%s);\n" % arg

    else:
        column_txt = None


    # (*) Line Number Increment Considerations
    if   counter.line_n_increment != E_Count.VOID:
        if counter.line_n_increment == 0:
            line_txt = ""
        else:
            line_txt = "__QUEX_IF_COUNT_LINES_ADD(%s);\n" % counter.line_n_increment

    elif counter.line_n_increment_by_lexeme_length:
        x = counter.line_n_increment_by_lexeme_length
        if x == 1: arg = "LexemeL"
        else:      arg = "LexemeL * %i" % x
        line_txt = "__QUEX_IF_COUNT_LINES_ADD(%s);\n" % arg

    else:
        line_txt = None

    return "__QUEX_COUNTER_SHIFT_VALUES(self.counter);\n" \
           + line_txt \
           + column_txt

