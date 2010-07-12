#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__BASE_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__BASE_I

#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/counter/Base>

#if         ! defined(__QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT)
#   include <quex/code_base/analyzer/counter/LineColumn.i>
#   else
#   include <quex/code_base/analyzer/counter/LineColumnIndentation.i>
#endif

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void
    QUEX_NAME(CounterBase_init)(QUEX_NAME(CounterBase)* me)
    {
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        me->_line_number_at_begin = (size_t)0;
        me->_line_number_at_end   = (size_t)1;
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->_column_number_at_begin = (size_t)0;
        me->_column_number_at_end   = (size_t)1; 
#       endif
    }

    QUEX_INLINE void             
    QUEX_NAME(CounterBase_shift_end_values_to_start_values)(QUEX_NAME(CounterBase)* me) 
    {
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        me->_line_number_at_begin   = me->_line_number_at_end;
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->_column_number_at_begin = me->_column_number_at_end;
#       endif
    }

    QUEX_INLINE void
    QUEX_NAME(CounterBase_count_newline_n_backwards)(QUEX_NAME(CounterBase)*       me, 
                                          QUEX_TYPE_CHARACTER* it,
                                          QUEX_TYPE_CHARACTER* Begin)
    /* NOTE: If *it == '\n' this function does **not** count it. The user must
     *       have increased the _line_number_at_end by hisself. This happens
     *       for performance reasons.                                             */
    {
        __quex_assert(it >= Begin);
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        /* investigate remaining part of the lexeme, i.e. before the last newline
         * (recall the lexeme is traced from the rear)                            */
        while( it != Begin ) {
            --it;
            if( *it == '\n' ) ++(me->_line_number_at_end); 
        }         
#       endif
    }

    QUEX_INLINE void 
    QUEX_NAME(CounterBase_print_this)(QUEX_NAME(CounterBase)* me)
    {
        __QUEX_STD_printf("   Counter:\n");
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        __QUEX_STD_printf("   _line_number_at_begin = %i;\n", (int)me->_line_number_at_begin);
        __QUEX_STD_printf("   _line_number_at_end   = %i;\n", (int)me->_line_number_at_end);
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __QUEX_STD_printf("   _column_number_at_begin = %i;\n", (int)me->_column_number_at_begin);
        __QUEX_STD_printf("   _column_number_at_end   = %i;\n", (int)me->_column_number_at_end);
#       endif
    }

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__BASE_I */

