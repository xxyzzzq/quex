#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _26
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

_19:
if( input < 0xB ) {
if     ( input == 0xA )  goto _8;
else if( input == 0x9 )  goto _9;
else                     goto _11;
} else {
if     ( input < 0x30 )  goto _11;
else if( input < 0x3A )  goto _10;
else                     goto _11;
}


    __quex_assert_no_passage();
_18:
    /* (13 from 24)  */
    __quex_debug_state(13);
    goto _19;


    __quex_assert_no_passage();
_13:
    /* (DROP_OUT from 14)  */
    __quex_debug("Drop-Out Catcher\n");
goto _2;



    __quex_assert_no_passage();
_15:
    /* (DROP_OUT from 16)  */
    __quex_debug("Drop-Out Catcher\n");
goto _4;


    __quex_assert_no_passage();
_17:
    /* (DROP_OUT from 18)  */
    __quex_debug("Drop-Out Catcher\n");
goto _6;


    __quex_assert_no_passage();
_14:
    /* (DROP_OUT from 15)  */
    __quex_debug("Drop-Out Catcher\n");
goto _3;


    __quex_assert_no_passage();
_16:
    /* (DROP_OUT from 17)  */
    __quex_debug("Drop-Out Catcher\n");
goto _5;


    __quex_assert_no_passage();
_10:
    /* (16 from 13)  */
    __quex_debug_state(16);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _15;


    __quex_assert_no_passage();
_11:
    /* (17 from 13)  */
    __quex_debug_state(17);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _16;


    __quex_assert_no_passage();

    /* (18 from 13)  */
    __quex_debug_state(18);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _17;


    __quex_assert_no_passage();
_8:
    /* (14 from 13)  */
    __quex_debug_state(14);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _13;


    __quex_assert_no_passage();
_9:
    /* (15 from 13)  */
    __quex_debug_state(15);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _14;

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_2:
    __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);

    __QUEX_IF_COUNT_COLUMNS((me->counter._column_number_at_end) = (size_t)1);

if( me->buffer._input_p != LexemeEnd ) goto _18;

goto _1;

_3:
    __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);

if( me->buffer._input_p != LexemeEnd ) goto _18;

goto _1;

_4:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);

if( me->buffer._input_p != LexemeEnd ) goto _18;

goto _1;

_5:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

if( me->buffer._input_p != LexemeEnd ) goto _18;

goto _1;

_6:
    __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);

goto _1;

_27: /* TERMINAL: FAILURE */
goto _6;
_1:
     __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
    return;
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
_26:
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   undef self
#   undef QUEX_LABEL_STATE_ROUTER
#    if ! defined(QUEX_OPTION_COMPUTED_GOTOS)
     goto _26; /* in QUEX_GOTO_STATE       */
#    endif
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _6;
    goto _27;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
