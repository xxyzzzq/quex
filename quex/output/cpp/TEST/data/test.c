#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _72
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    QUEX_TYPE_GOTO_LABEL           target_state_else_index        = QUEX_GOTO_LABEL_VOID;
    QUEX_TYPE_GOTO_LABEL           target_state_index             = QUEX_GOTO_LABEL_VOID;
    QUEX_TYPE_CHARACTER_POSITION   character_begin_p              = (QUEX_TYPE_CHARACTER_POSITION)0x0;
    (void)me;
    __QUEX_IF_COUNT_SHIFT_VALUES();
    /* Allow LexemeBegin == LexemeEnd (e.g. END_OF_STREAM)
     * => Caller does not need to check
     * BUT, if so quit immediately after 'shift values'. */
    __quex_assert(LexemeBegin <= LexemeEnd);
    if(LexemeBegin == LexemeEnd) return;
    me->buffer._input_p = LexemeBegin;

    /* (93 from NONE)  */
    __quex_debug("Init State\n");
    __quex_debug_state(93);
    input = *(me->buffer._input_p);

_36:
    character_begin_p = (me->buffer._input_p);


if( input < 0xC2 ) {
if( input < 0xB ) {
if     ( input == 0xA )  goto _20;
else if( input == 0x9 )  goto _13;
else                     goto _19;
} else {
if     ( input < 0x30 )  goto _19;
else if( input < 0x3A )  goto _17;
else if( input < 0x80 )  goto _19;
else                     goto _29;
}
} else {
if( input < 0xF1 ) {
if( input < 0xE1 ) {
if( input == 0xE0 )  goto _14;
else                 goto _9;
} else {
if( input == 0xF0 )  goto _16;
else                 goto _8;
}
} else {
if( input < 0xF4 ) {
if( input == 0xF1 )  goto _18;
else                 goto _15;
} else {
if( input < 0xF8 )  goto _7;
else                goto _29;
}
}
}


    __quex_assert_no_passage();
_34:
    /* (93 from 142)  */
    __quex_debug_state(93);
    goto _36;


    __quex_assert_no_passage();
_32:
    /* (DROP_OUT from 115) (DROP_OUT from 113) (DROP_OUT from 135) (DROP_OUT from 114) (DROP_OUT from 104)  */
    __quex_debug("Drop-Out Catcher\n");

goto _3;
_37:


    __quex_assert_no_passage();
_31:
    /* (DROP_OUT from 102)  */
    __quex_debug("Drop-Out Catcher\n");
goto _5;


    __quex_assert_no_passage();
_33:
    /* (DROP_OUT from 107)  */
    __quex_debug("Drop-Out Catcher\n");
goto _6;


    __quex_assert_no_passage();
_30:
    /* (DROP_OUT from 94)  */
    __quex_debug("Drop-Out Catcher\n");
goto _4;


    __quex_assert_no_passage();
_29:
    /* (DROP_OUT from 98) (DROP_OUT from 111) (DROP_OUT from 93) (DROP_OUT from 130) (DROP_OUT from 112) (DROP_OUT from 122) (DROP_OUT from 134) (DROP_OUT from 109) (DROP_OUT from 103) (DROP_OUT from 100) (DROP_OUT from 128) (DROP_OUT from 97) (DROP_OUT from 110) (DROP_OUT from 132) (DROP_OUT from 129)  */
    __quex_debug("Drop-Out Catcher\n");
    me->buffer._input_p = me->buffer._lexeme_start_p + 1; 

goto _39;
    goto _37;


    __quex_assert_no_passage();
_7:
    /* (128 from 122) (128 from 93)  */
    __quex_debug_state(128);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _8;
else                      goto _29;


    __quex_assert_no_passage();
_8:
    /* (129 from 128) (129 from 93)  */
    __quex_debug_state(129);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _9;
else                      goto _29;


    __quex_assert_no_passage();
_9:
    /* (130 from 93) (130 from 97) (130 from 129)  */
    __quex_debug_state(130);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _19;
else                      goto _29;


    __quex_assert_no_passage();
_10:
    /* (132 from 98)  */
    __quex_debug_state(132);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _11;
else                      goto _29;


    __quex_assert_no_passage();
_11:
    /* (134 from 132)  */
    __quex_debug_state(134);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _12;
else                      goto _29;


    __quex_assert_no_passage();
_12:
    /* (135 from 134) (135 from 114) (135 from 113)  */
    __quex_debug_state(135);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _32;
else if( input >= 0x80 )  goto _19;
else                      goto _32;


    __quex_assert_no_passage();
_13:
    /* (94 from 93)  */
    __quex_debug_state(94);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _30;


    __quex_assert_no_passage();
_14:
    /* (97 from 93)  */
    __quex_debug_state(97);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0xA0 )  goto _9;
else                      goto _29;


    __quex_assert_no_passage();
_15:
    /* (98 from 93) (98 from 100)  */
    __quex_debug_state(98);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _10;
else                      goto _29;


    __quex_assert_no_passage();
_16:
    /* (100 from 93)  */
    __quex_debug_state(100);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if( input < 0x88 ) {
if( input >= 0x84 )  goto _28;
else                 goto _29;
} else {
if     ( input < 0x90 )  goto _15;
else if( input < 0xC0 )  goto _21;
else                     goto _29;
}


    __quex_assert_no_passage();
_17:
    /* (102 from 93)  */
    __quex_debug_state(102);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _31;


    __quex_assert_no_passage();
_18:
    /* (103 from 93)  */
    __quex_debug_state(103);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input == 0xBF )  goto _22;
else if( input >= 0x80 )  goto _21;
else                      goto _29;


    __quex_assert_no_passage();
_19:
    /* (104 from 115) (104 from 130) (104 from 135) (104 from 93)  */
    __quex_debug_state(104);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _32;


    __quex_assert_no_passage();
_20:
    /* (107 from 93)  */
    __quex_debug_state(107);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


goto _33;


    __quex_assert_no_passage();
_21:
    /* (109 from 100) (109 from 103)  */
    __quex_debug_state(109);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _23;
else                      goto _29;


    __quex_assert_no_passage();
_22:
    /* (110 from 103)  */
    __quex_debug_state(110);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input == 0xBF )  goto _24;
else if( input >= 0x80 )  goto _23;
else                      goto _29;


    __quex_assert_no_passage();
_23:
    /* (111 from 110) (111 from 109)  */
    __quex_debug_state(111);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _25;
else                      goto _29;


    __quex_assert_no_passage();
_24:
    /* (112 from 110)  */
    __quex_debug_state(112);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input == 0xBF )  goto _26;
else if( input >= 0x80 )  goto _25;
else                      goto _29;


    __quex_assert_no_passage();
_25:
    /* (113 from 112) (113 from 111)  */
    __quex_debug_state(113);

    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _32;
else if( input >= 0x80 )  goto _12;
else                      goto _32;


    __quex_assert_no_passage();
_26:
    /* (114 from 112)  */
    __quex_debug_state(114);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _32;
else if( input == 0xBF )  goto _27;
else if( input >= 0x80 )  goto _12;
else                      goto _32;


    __quex_assert_no_passage();
_27:
    /* (115 from 114)  */
    __quex_debug_state(115);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xBF )  goto _32;
else if( input >= 0x80 )  goto _19;
else                      goto _32;


    __quex_assert_no_passage();
_28:
    /* (122 from 100)  */
    __quex_debug_state(122);
    ++(me->buffer._input_p);

    input = *(me->buffer._input_p);


if     ( input >= 0xC0 )  goto _29;
else if( input >= 0x80 )  goto _7;
else                      goto _29;

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_6:
    __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);

    __QUEX_IF_COUNT_COLUMNS((me->counter._column_number_at_end) = (size_t)1);

if( me->buffer._input_p != LexemeEnd ) goto _34;

goto _1;

_4:
    __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);

if( me->buffer._input_p != LexemeEnd ) goto _34;

goto _1;

_5:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);

if( me->buffer._input_p != LexemeEnd ) goto _34;

goto _1;

_3:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

if( me->buffer._input_p != LexemeEnd ) goto _34;

goto _1;

_71:
    __quex_debug("* TERMINAL <BEYOND>\n");
    (me->buffer._input_p) = character_begin_p;

goto _1;

_39: /* TERMINAL: FAILURE */
goto _71;
_1:
     __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
    return;
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
_72:
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   undef self
#   undef QUEX_LABEL_STATE_ROUTER
#    if ! defined(QUEX_OPTION_COMPUTED_GOTOS)
     goto _72; /* in QUEX_GOTO_STATE       */
#    endif
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _71;
    goto _39;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
