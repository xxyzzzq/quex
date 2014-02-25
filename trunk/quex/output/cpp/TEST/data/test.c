#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    QUEX_TYPE_CHARACTER_POSITION   reference_p                    = (QUEX_TYPE_CHARACTER_POSITION)0x0;
    (void)me;
    __QUEX_IF_COUNT_SHIFT_VALUES();
    /* Allow LexemeBegin == LexemeEnd (e.g. END_OF_STREAM)
     * => Caller does not need to check
     * BUT, if so quit immediately after 'shift values'. */
    __quex_assert(LexemeBegin <= LexemeEnd);
    if(LexemeBegin == LexemeEnd) return;
    me->buffer._input_p = LexemeBegin;
 /* (2 from NONE) */
    input = *(me->buffer._input_p);
__QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);

_8:

    __quex_debug("Init State\n");
    __quex_debug_state(2);
    if     ( input >= 0xB ) goto _5; 
    else if( input == 0xA ) goto _3; 
    else if( input == 0x9 ) goto _4; 
    else                    goto _5;

    __quex_debug_drop_out(2);
goto _1;


    __quex_assert_no_passage();
_7: /* (2 from 7) */
    goto _8;



    __quex_assert_no_passage();
_3: /* (3 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _11;

_11:

    __quex_debug_state(3);
    __quex_debug_drop_out(3);
goto _13;

    __quex_assert_no_passage();
_4: /* (4 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _14;

_14:

    __quex_debug_state(4);
    __quex_debug_drop_out(4);
goto _16;

    __quex_assert_no_passage();
_5: /* (5 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _17;

_17:

    __quex_debug_state(5);
    __quex_debug_drop_out(5);
goto _19;

    __quex_assert_no_passage();
 /* (6 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _20;

_20:

    __quex_debug_state(6);
    __quex_debug_drop_out(6);
goto _22;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_13: __quex_debug("* TERMINAL \n");
    __QUEX_IF_COUNT_LINES_ADD((size_t)1);
    __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
    __QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);
    if( me->buffer._input_p != LexemeEnd ) goto _7;;
    goto _1;

_16: __quex_debug("* TERMINAL \n");
    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)((me->buffer._input_p - reference_p - 1)));
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4);
    __QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);
    if( me->buffer._input_p != LexemeEnd ) goto _7;;
    goto _1;

_19: __quex_debug("* TERMINAL \n");
    if( me->buffer._input_p != LexemeEnd ) goto _7;;
    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)((me->buffer._input_p - reference_p)));
    goto _1;

_22: __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);
    goto _1;

_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
}
#endif /* __QUEX_OPTION_COUNTER */
