#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _29
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    QUEX_TYPE_GOTO_LABEL           target_state_else_index        = QUEX_GOTO_LABEL_VOID;
    QUEX_TYPE_GOTO_LABEL           target_state_index             = QUEX_GOTO_LABEL_VOID;
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

_15:

    __quex_debug("Init State\n");
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

__quex_assert_no_passage();


    __quex_assert_no_passage();
_14: /* (14 from 20) */
    goto _15;



    __quex_assert_no_passage();
 /* (DROP_OUT from 14) */
    me->buffer._input_p = me->buffer._lexeme_start_p + 1; 

goto _18;    goto _17;

_9: /* (DROP_OUT from 15) */
    goto _19;    goto _17;

_10: /* (DROP_OUT from 16) */
    goto _20;    goto _17;

_11: /* (DROP_OUT from 17) */
    goto _21;    goto _17;

_12: /* (DROP_OUT from 18) */
    goto _22;    goto _17;

_13: /* (DROP_OUT from 19) */
    goto _23;    goto _17;

_17:

    __quex_debug("Drop-Out Catcher\n");

__quex_assert_no_passage();


    __quex_assert_no_passage();
_4: /* (16 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _24;

_24:

    __quex_debug_state(16);
goto _10;

    __quex_assert_no_passage();
_5: /* (17 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _25;

_25:

    __quex_debug_state(17);
goto _11;

    __quex_assert_no_passage();
_6: /* (18 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _26;

_26:

    __quex_debug_state(18);
goto _12;

    __quex_assert_no_passage();
 /* (19 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _27;

_27:

    __quex_debug_state(19);
goto _13;

    __quex_assert_no_passage();
_3: /* (15 from 14) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _28;

_28:

    __quex_debug_state(15);
goto _9;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_19: __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _14;
goto _1;
_20: __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);
if( me->buffer._input_p != LexemeEnd ) goto _14;
goto _1;
_21: __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);
if( me->buffer._input_p != LexemeEnd ) goto _14;
goto _1;
_22: __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _14;
goto _1;
_23: __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);
goto _1;
_18:
    goto _23;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
#  undef QUEX_LABEL_STATE_ROUTER
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _23;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
