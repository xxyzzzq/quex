#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    (void)me;
    __QUEX_IF_COUNT_SHIFT_VALUES();
    /* Allow LexemeBegin == LexemeEnd (e.g. END_OF_STREAM)
     * => Caller does not need to check
     * BUT, if so quit immediately after 'shift values'. */
    __quex_assert(LexemeBegin <= LexemeEnd);
    if(LexemeBegin == LexemeEnd) return;
    me->buffer._input_p = LexemeBegin;
 /* (34 from NONE) */
    input = *(me->buffer._input_p);

_10:

    __quex_debug("Init State\n");
    __quex_debug_state(34);
    if( input < 0x6F ) {
        if( input == 0x6E ) {
            goto _5;
        
} else if( input >= 0x4D ) {
            goto _7;
        
} else if( input == 0x4C ) {
            goto _3;
        } else {
            goto _7;
        
}
    } else {
        if( input == 0x6F ) {
            goto _6;
        
} else if( input < 0x7E ) {
            goto _7;
        
} else if( input == 0x7E ) {
            goto _4;
        
} else if( input < 0x100 ) {
            goto _7;
        } else {

        
}
    
}

    __quex_debug_drop_out(34);
goto _1;


    __quex_assert_no_passage();
_9: /* (34 from 45) */
    goto _10;



    __quex_assert_no_passage();
_3: /* (35 from 34) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _12;

_12:

    __quex_debug_state(35);
    __quex_debug_drop_out(35);
goto _14;

    __quex_assert_no_passage();
_4: /* (36 from 34) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _15;

_15:

    __quex_debug_state(36);
    __quex_debug_drop_out(36);
goto _17;

    __quex_assert_no_passage();
_5: /* (37 from 34) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _18;

_18:

    __quex_debug_state(37);
    __quex_debug_drop_out(37);
goto _20;

    __quex_assert_no_passage();
_6: /* (38 from 34) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _21;

_21:

    __quex_debug_state(38);
    __quex_debug_drop_out(38);
goto _23;

    __quex_assert_no_passage();
_7: /* (43 from 34) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _24;

_24:

    __quex_debug_state(43);
    __quex_debug_drop_out(43);
goto _26;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_14: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)0);
if( me->buffer._input_p != LexemeEnd ) goto _9;
goto _1;
_17: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _9;
goto _1;
_20: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);
if( me->buffer._input_p != LexemeEnd ) goto _9;
goto _1;
_23: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);
if( me->buffer._input_p != LexemeEnd ) goto _9;
goto _1;
_26: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _9;
goto _1;
_31: __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);
goto _1;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
}
#endif /* __QUEX_OPTION_COUNTER */
