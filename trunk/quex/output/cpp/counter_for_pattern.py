"""____________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
_______________________________________________________________________________
"""
from   quex.engine.generator.state.transition.code  import TextTransitionCode
import quex.engine.generator.state.transition.core  as     transition_map_coder
import quex.engine.generator.state_machine_coder    as     state_machine_coder
from   quex.engine.generator.base                   import get_combined_state_machine
from   quex.engine.generator.languages.address      import get_plain_strings
from   quex.engine.generator.action_info            import CodeFragment, \
                                                           PatternActionInfo
from   quex.engine.state_machine.core               import StateMachine
import quex.engine.analyzer.core                    as     analyzer_generator
import quex.engine.analyzer.transition_map          as     transition_map_tool
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.utf8                             import unicode_to_utf8
from   quex.engine.misc.string_handling             import blue_print

from   quex.blackboard import E_Count, \
                              setup as Setup, \
                              DefaultCounterFunctionDB

from   itertools import islice
from   copy      import deepcopy
import sys

def get(ThePattern, EOF_ActionF):
    """Line and column number actions for a pattern.

    Generates code to adapt line and column number counters when a pattern
    has matched. It tries to do as much as possible beforehand. That is, if
    the line and column increments are determined from the pattern structure
    it produces very simple and fast instructions.

    This function assumes that the 'count_info' for a pattern has been
    determined before, based on the 'counted_db'.
    
    If the adaption of line and column numbers cannot be derived from the 
    pattern itself or the lexeme length, then a call to the 'default_counter'
    is implemented. 

    ---------------------------------------------------------------------------

    RETURN: Verdict, CounterCode

        Verdict == True  --> Pattern requires run-time counting. Default
                             counter implementation required.
                   False --> It was possible to determine the increments
                             based on the pattern's structure. Non run-
                             time counting is necessary.

        CounterCode = Code to be prefixed in from of the action.
    ---------------------------------------------------------------------------
    
    The increment of line number and column number may be determined by
    'ThePattern' itself. For example the pattern "\n\n" increments the line
    number always by 2. The pattern "\n+" however increments the line number
    depending on how many '\n' it matches at runtime. These considerations
    where done by means of 

              quex.engine.state_machine.character_counter.do(...)

    It is called inside the 'prepare_count_info()' member function of the
    pattern at the time when it is communicated to the 'Mode' object from the
    'ModeDescription' object in:

              quex.input.files.mode.Mode.__init__(...)

    As a consequence of a call to '.prepare_count_info()', the pattern's 'count'
    object must be set to something not 'None'. If it is 'None', this means
    that the 'prepare_count_info()' function has not been called for it.  
    ---------------------------------------------------------------------------
    """
    LanguageDB = Setup.language_db

    # (*) Trivial Cases _______________________________________________________
    if EOF_ActionF:
        txt = [1, "__QUEX_IF_COUNT_SHIFT_VALUES();\n" ]

        return False, txt

    if ThePattern is None:
        # 'on_failure' ... count any appearing character
        return True, [1, "__QUEX_COUNT_VOID(&self, LexemeBegin, LexemeEnd);\n"]

    counter = ThePattern.count_info()

    # (*) Default Character Counter ___________________________________________
    #
    #     Used when the increments and/or setting cannot be derived from the 
    #     pattern itself. That is, if one of the following is VOID:
    if         counter.line_n_increment_by_lexeme_length   == E_Count.VOID \
       or (    counter.column_n_increment_by_lexeme_length == E_Count.VOID \
           and counter.grid_step_size_by_lexeme_length     == E_Count.VOID):
        return True, [1, "__QUEX_COUNT_VOID(&self, LexemeBegin, LexemeEnd);\n"]

    # (*) Determine Line and Column Number Count ______________________________
    #    
    #     Both, for line and column number considerations the same rules hold.
    #     Those rules are defined in 'get_increment()' as shown below.
    #
    def get_increment(Increment, IncrementByLexemeLength, HelpStr):

        if IncrementByLexemeLength == 0 or Increment == 0:
            return ""
        elif Increment != E_Count.VOID:
            arg = "%i" % Increment
        elif IncrementByLexemeLength == 1: 
            arg = "LexemeL"
        else:
            arg = "LexemeL * %i" % IncrementByLexemeLength

        return [1, "__QUEX_IF_COUNT_SHIFT_VALUES();\n",
                1, "__QUEX_IF_COUNT_%s_ADD(%s);\n" % (HelpStr, arg)]

    # -- Line Number Count
    txt = []
    txt.extend(get_increment(counter.line_n_increment, 
                             counter.line_n_increment_by_lexeme_length, 
                             "LINES"))

    # -- Column Number Count
    if  counter.column_index != E_Count.VOID:
        txt.extend([1, "__QUEX_IF_COUNT_COLUMNS_SET(%i);\n" % (counter.column_index + 1)])

    elif counter.column_n_increment_by_lexeme_length != E_Count.VOID:
        txt.extend(get_increment(counter.column_n_increment, 
                                 counter.column_n_increment_by_lexeme_length, 
                                 "COLUMNS"))

    else:
        # Following assert results from entry check against 'VOID'
        assert counter.grid_step_size_by_lexeme_length != E_Count.VOID

        if counter.grid_step_n == E_Count.VOID: grid_step_n = "LexemeL"
        else:                                   grid_step_n = counter.grid_step_n

        txt.extend([1, "__QUEX_IF_COUNT_SHIFT_VALUES();\n"])
        txt.extend(LanguageDB.GRID_STEP("self.counter._column_number_at_end", "size_t",
                                        counter.grid_step_size_by_lexeme_length, 
                                        grid_step_n, IfMacro="__QUEX_IF_COUNT_COLUMNS"))
        txt.append("\n")

    return False, txt
