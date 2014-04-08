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
 /* (14 from NONE) */
    input = *(me->buffer._input_p);

_9:

    __quex_debug("Init State\n");
    __quex_debug_state(14);
    if( input < 0xB ) {
        switch( input ) {
            case 0x0: 
            case 0x1: 
            case 0x2: 
            case 0x3: 
            case 0x4: 
            case 0x5: 
            case 0x6: 
            case 0x7: 
            case 0x8: goto _6;
            case 0x9: goto _4;
            case 0xA: goto _3;

        }
    } else {
        if( input < 0x30 ) {
            goto _6;
        
} else if( input < 0x3A ) {
            goto _5;
        } else {
            goto _6;
        
}
    
}

    __quex_debug_drop_out(14);
goto _1;


    __quex_assert_no_passage();
_8: /* (14 from 20) */
    goto _9;



    __quex_assert_no_passage();
_4: /* (16 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _12;

_12:

    __quex_debug_state(16);
    __quex_debug_drop_out(16);
goto _14;

    __quex_assert_no_passage();
_5: /* (17 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _15;

_15:

    __quex_debug_state(17);
    __quex_debug_drop_out(17);
goto _17;

    __quex_assert_no_passage();
_6: /* (18 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _18;

_18:

    __quex_debug_state(18);
    __quex_debug_drop_out(18);
goto _20;

    __quex_assert_no_passage();
 /* (19 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _21;

_21:

    __quex_debug_state(19);
    __quex_debug_drop_out(19);
goto _23;

    __quex_assert_no_passage();
_3: /* (15 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _24;

_24:

    __quex_debug_state(15);
    __quex_debug_drop_out(15);
goto _26;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_26: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _8;
goto _1;
_14: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);
if( me->buffer._input_p != LexemeEnd ) goto _8;
goto _1;
_17: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);
if( me->buffer._input_p != LexemeEnd ) goto _8;
goto _1;
_20: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _8;
goto _1;
_23: __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);
goto _1;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _23;
}
#endif /* __QUEX_OPTION_COUNTER */
