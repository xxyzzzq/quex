#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _23
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

    /* (13 from NONE)  */
    __quex_debug("Init State\n");
    __quex_debug_state(13);
    input = *(me->buffer._input_p);

_16:
switch( input ) {
case 0x9: goto _10;
case 0xA: goto _9;
case 0x30: case 0x31: case 0x32: case 0x33: case 0x34: case 0x35: case 0x36: case 0x37: 
case 0x38: case 0x39: goto _7;
default: goto _8;
}


    __quex_assert_no_passage();
_15:
    /* (13 from 22)  */
    __quex_debug_state(13);
    goto _16;


    __quex_assert_no_passage();
_11:
    /* (DROP_OUT from 14)  */
    __quex_debug("Drop-Out Catcher\n");
goto _5;



    __quex_assert_no_passage();
_13:
    /* (DROP_OUT from 16)  */
    __quex_debug("Drop-Out Catcher\n");
goto _3;


    __quex_assert_no_passage();
_12:
    /* (DROP_OUT from 15)  */
    __quex_debug("Drop-Out Catcher\n");
goto _6;


    __quex_assert_no_passage();
_14:
    /* (DROP_OUT from 17)  */
    __quex_debug("Drop-Out Catcher\n");
goto _4;


    __quex_assert_no_passage();
_7:
    /* (16 from 13)  */
    __quex_debug_state(16);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _13;


    __quex_assert_no_passage();
_8:
    /* (17 from 13)  */
    __quex_debug_state(17);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _14;


    __quex_assert_no_passage();
_9:
    /* (14 from 13)  */
    __quex_debug_state(14);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _11;


    __quex_assert_no_passage();
_10:
    /* (15 from 13)  */
    __quex_debug_state(15);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _12;

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_5:
    __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);

    __QUEX_IF_COUNT_COLUMNS((me->counter._column_number_at_end) = (size_t)1);

if( me->buffer._input_p != LexemeEnd ) goto _15;

goto _1;

_6:
    __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);

if( me->buffer._input_p != LexemeEnd ) goto _15;

goto _1;

_3:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);

if( me->buffer._input_p != LexemeEnd ) goto _15;

goto _1;

_4:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

if( me->buffer._input_p != LexemeEnd ) goto _15;

goto _1;

_22:
    __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);

goto _1;

_24: /* TERMINAL: FAILURE */
goto _22;
_1:
     __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
    return;
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
_23:
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   undef self
#   undef QUEX_LABEL_STATE_ROUTER
#    if ! defined(QUEX_OPTION_COMPUTED_GOTOS)
     goto _23; /* in QUEX_GOTO_STATE       */
#    endif
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _22;
    goto _24;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
