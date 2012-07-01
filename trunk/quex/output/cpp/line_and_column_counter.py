# (C) 2012 Frank-Rene Schaefer

def do(ThePattern, EOF_ActionF):
    """Prepare additional actions which are required for line and column
    number counting. 
    
    The '.newline_n' and '.column_n' of a given 'Pattern' may be given by the
    pattern itself. For example the pattern "\n\n" increments the line number
    always by 2. The pattern "\n+" however increments the line number depending
    on how many '\n' it matches at runtime. These considerations where done
    by means of 

              quex.engine.state_machine.character_counter.do(...)

    at the time when the Pattern object was constructed in 

              class quex.input.regular_expression.construct.Pattern

    Depending on the newline_n and column_n increment being pre-determined,
    the counting behavior may be adapted. The following options exist:

        __QUEX_COUNT_END_OF_STREAM_EVENT(me)
        __QUEX_COUNT_VOID(me)
        __QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_VOID(me, NewlineN) 
        __QUEX_COUNT_NEWLINE_N_ZERO_COLUMN_N_FIXED(me, ColumnN) 

    Their definition appears in 

             $QUEX_PATH/quex/code_base/definitions

    Where they are mapped to macros and functions which accomplish the job.

    """
    global LanguageDB

    if EOF_ActionF:
        return "__QUEX_COUNT_END_OF_STREAM_EVENT(self.counter);"

    if ThePattern is None:
        return "__QUEX_COUNT_VOID(self.counter);"

    newline_n   = ThePattern.newline_n
    character_n = ThePattern.character_n
    grid        = ThePattern.count.grid
    line_ipc    = ThePattern.count.increment_line_n_per_char
    column_ipc  = ThePattern.count.increment_column_n_per_char

    if   newline_n == E_Count.VOID:
        # Run the general algorithm, since not even the number of newlines in the 
        # pattern can be determined directly from the pattern
        return "__QUEX_COUNT_VOID(self.counter);"

    elif newline_n != 0:
        if ThePattern.sm.get_ending_character_set().contains_only(ord('\n')):
            # A pattern that ends with newline, lets the next column start at one.
            return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_ZERO(self.counter, %i);" % newline_n
        # TODO: Try to determine number of characters backwards to newline directly
        #       from the pattern state machine. (Those seldom cases won't bring much
        #       speed-up)
        return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_VOID(self.counter, %i);" % newline_n

    # Lexeme does not contain newline --> count only columns
    if character_n == E_Count.VOID: incr_str = "LexemeL"
    else:                           incr_str = "%i" % int(character_n)
    return "__QUEX_COUNT_NEWLINE_N_ZERO_COLUMN_N_FIXED(self.counter, %s);" % incr_str

def __new_do(ThePattern, EOF_ActionF):
    """Prepare additional actions around a pattern action which are required 
    for line and column number counting. 
    
    The '.newline_n' and '.column_n' of a given 'Pattern' may be given by the
    pattern itself. For example the pattern "\n\n" increments the line number
    always by 2. The pattern "\n+" however increments the line number depending
    on how many '\n' it matches at runtime. These considerations where done
    by means of 

              quex.engine.state_machine.character_counter.do(...)

    at the time when the Pattern object was constructed in 

              class quex.input.regular_expression.construct.Pattern

    Depending on the newline_n and column_n increment being pre-determined,
    the counting behavior may be adapted. The following options exist:

            __QUEX_COUNT_NEWLINE_*

            __QUEX_COUNT_COLUMN_*


    An increment that can be determined by the length of the lexeme is passed
    as 'LexemeL * Increment' of an 'N' function.

            __QUEX_COUNT_NEWLINE_X
            __QUEX_COUNT_NEWLINE_X
            __QUEX_COUNT_NEWLINE_N
            __QUEX_COUNT_NEWLINE_N
            __QUEX_COUNT_NEWLINE_N
            __QUEX_COUNT_NEWLINE_0
            __QUEX_COUNT_NEWLINE_0
            __QUEX_COUNT_NEWLINE_0

    Their definition appears in 

             $QUEX_PATH/quex/code_base/definitions

    Where they are mapped to macros and functions which accomplish the job.
    """
    global LanguageDB

    if EOF_ActionF:
        return "__QUEX_COUNT_END_OF_STREAM_EVENT(self.counter);"

    if ThePattern is None:
        return "__QUEX_COUNT_NEWLINE_X_COLUMN_X_GRID_X(self.counter);"

    if ThePattern.count.line_n == 0:
        return __pattern_without_newline(ThePattern.count)
    else:
        return __pattern_with_newline(ThePattern.count)


def __pattern_with_newline(Count):
    columns_involved_f       = (Count.column_n != 0 or Count.grid != E_Count.NONE)
    line_n_increment_fixed_f = (Count.increment_line_n_per_char != E_Count.VOID)

    if Count.line_n == E_Count.VOID:
        if columns_involved_f:
            # Column and line numbers appear in the pattern and nothing can
            # be determined beforehand. Thus, run the general count algorithm.
            return "__QUEX_COUNT_VOID(self.counter);"
        else:
            # There are solely newline characters involved in the pattern.
            # Thus, the line number increment can be determined by the number
            # of newline characters, IF all have the same increment.
            if line_n_increment_fixed_f:
                assert isinstance(Count.increment_line_n_per_char, (int, long))
                return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_ZERO(self.counter, LexemeL * %i);" \
                       % Count.increment_line_n_per_char
            else:
                return "__QUEX_COUNT_VOID(self.counter);"
    else:
        isinstance(Count.line_n, (int, long))
        # Line numbers do not have to be counted.
        if not columns_involved_f:
            if line_n_increment_fixed_f:
                return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_ZERO(self.counter, %i);" \
                       % (Count.line_n * Count.increment_line_n_per_char)
            elif grid == E_Count.NONE:
                return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_VOID(self.counter);"
            else:
                return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_VOID(self.counter);"

def __pattern_without_newline(Count):
        


    assert isinstance(Count.line_n, (int, long))
    # line_n == integer means, that the number of newlines in the pattern is fixed.

    if ThePattern.sm.get_ending_character_set().contains_only(ord('\n')):
        # A pattern that ends with newline, lets the next column start at one.
        return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_ZERO(self.counter, %i);" % Count.line_n

    # TODO: Try to determine number of characters backwards to newline directly
    #       from the pattern state machine. (Those seldom cases won't bring much
    #       speed-up)
    return "__QUEX_COUNT_NEWLINE_N_FIXED_COLUMN_N_VOID(self.counter, %i);" % Count.line_n

def __pattern_without_newline(Count):
    # Lexeme does not contain newline --> count only columns
    if Count.column_n == E_Count.VOID: incr_str = "LexemeL"
    else:                              incr_str = "%i" % int(character_n)
    return "__QUEX_COUNT_NEWLINE_N_ZERO_COLUMN_N_FIXED(self.counter, %s);" % incr_str

