#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_LEXATOM* LexemeBegin, QUEX_TYPE_LEXATOM* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _47
    QUEX_TYPE_LEXATOM*             lexatom_begin_p                = (QUEX_TYPE_LEXATOM*)0x0;
    QUEX_TYPE_LEXATOM              input                          = (QUEX_TYPE_LEXATOM)(0x00);
    QUEX_TYPE_GOTO_LABEL           target_state_else_index        = QUEX_GOTO_LABEL_VOID;
    QUEX_TYPE_GOTO_LABEL           target_state_index             = QUEX_GOTO_LABEL_VOID;
    (void)me;
    __QUEX_IF_COUNT_SHIFT_VALUES();
    /* Allow LexemeBegin == LexemeEnd (e.g. END_OF_STREAM)
     * => Caller does not need to check
     * BUT, if so quit immediately after 'shift values'. */
    __quex_assert(LexemeBegin <= LexemeEnd);
    if(LexemeBegin == LexemeEnd) return;
    me->buffer._read_p = LexemeBegin;

    /* (117 from BEFORE_ENTRY)  */
    input = *(me->buffer._read_p);

_22:
    lexatom_begin_p = (me->buffer._read_p);


    __quex_debug("Init State\n");
    __quex_debug_state(117);
switch( input ) {
case 0x9: goto _5;
case 0xA: goto _10;
case 0x30: case 0x31: case 0x32: case 0x33: case 0x34: case 0x35: case 0x36: case 0x37: 
case 0x38: case 0x39: goto _4;
case 0x80: case 0x81: case 0x82: case 0x83: case 0x84: case 0x85: case 0x86: case 0x87: 
case 0x88: case 0x89: case 0x8A: case 0x8B: case 0x8C: case 0x8D: case 0x8E: case 0x8F: 
case 0x90: case 0x91: case 0x92: case 0x93: case 0x94: case 0x95: case 0x96: case 0x97: 
case 0x98: case 0x99: case 0x9A: case 0x9B: case 0x9C: case 0x9D: case 0x9E: case 0x9F: 
case 0xA0: case 0xA1: case 0xA2: case 0xA3: case 0xA4: case 0xA5: case 0xA6: case 0xA7: 
case 0xA8: case 0xA9: case 0xAA: case 0xAB: case 0xAC: case 0xAD: case 0xAE: case 0xAF: 
case 0xB0: case 0xB1: case 0xB2: case 0xB3: case 0xB4: case 0xB5: case 0xB6: case 0xB7: 
case 0xB8: case 0xB9: case 0xBA: case 0xBB: case 0xBC: case 0xBD: case 0xBE: case 0xBF: goto _13;
case 0xC0: case 0xC1: goto _14;
case 0xC2: case 0xC3: case 0xC4: case 0xC5: case 0xC6: case 0xC7: 
case 0xC8: case 0xC9: case 0xCA: case 0xCB: case 0xCC: case 0xCD: case 0xCE: case 0xCF: 
case 0xD0: case 0xD1: case 0xD2: case 0xD3: case 0xD4: case 0xD5: case 0xD6: case 0xD7: 
case 0xD8: case 0xD9: case 0xDA: case 0xDB: case 0xDC: case 0xDD: case 0xDE: case 0xDF: goto _8;
case 0xE0: goto _11;
case 0xE1: case 0xE2: case 0xE3: case 0xE4: case 0xE5: case 0xE6: case 0xE7: 
case 0xE8: case 0xE9: case 0xEA: case 0xEB: case 0xEC: case 0xED: case 0xEE: case 0xEF: goto _7;
case 0xF0: goto _3;
case 0xF1: case 0xF2: case 0xF3: goto _9;
case 0xF4: goto _12;
case 0xF5: case 0xF6: case 0xF7: 
case 0xF8: case 0xF9: case 0xFA: case 0xFB: case 0xFC: case 0xFD: goto _14;
case 0xFE: case 0xFF: goto _13;
default: goto _6;
}


    __quex_assert_no_passage();
_20:
    /* (117 from 129)  */
    goto _22;


    __quex_assert_no_passage();
_14:
    /* (DROP_OUT from 117) (DROP_OUT from 125) (DROP_OUT from 128) (DROP_OUT from 126)  */

        me->buffer._read_p = me->buffer._lexeme_start_p + 1;
goto _25;

    __quex_debug("Drop-Out Catcher\n");


    __quex_assert_no_passage();
_19:
    /* (DROP_OUT from 127)  */
    goto _26;


    __quex_assert_no_passage();
_18:
    /* (DROP_OUT from 124)  */
    goto _27;


    __quex_assert_no_passage();
_17:
    /* (DROP_OUT from 120)  */
    goto _28;


    __quex_assert_no_passage();
_16:
    /* (DROP_OUT from 119)  */
    goto _29;


    __quex_assert_no_passage();
_15:
    /* (DROP_OUT from 118)  */
    goto _30;


    __quex_assert_no_passage();
_3:
    /* (128 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(128);
if     ( input >= 0xC0 )  goto _13;
else if( input >= 0x90 )  goto _7;
else if( input >= 0x80 )  goto _14;
else                      goto _13;


    __quex_assert_no_passage();
_4:
    /* (118 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(118);
goto _15;


    __quex_assert_no_passage();
_5:
    /* (119 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(119);
goto _16;


    __quex_assert_no_passage();
_6:
    /* (120 from 122) (120 from 117)  */

    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(120);
goto _17;


    __quex_assert_no_passage();
_7:
    /* (121 from 128) (121 from 123) (121 from 117) (121 from 126)  */

    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(121);
if     ( input >= 0xC0 )  goto _13;
else if( input >= 0x80 )  goto _8;
else                      goto _13;


    __quex_assert_no_passage();
_8:
    /* (122 from 117) (122 from 125) (122 from 121)  */

    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(122);
if     ( input >= 0xC0 )  goto _13;
else if( input >= 0x80 )  goto _6;
else                      goto _13;


    __quex_assert_no_passage();
_9:
    /* (123 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(123);
if     ( input >= 0xC0 )  goto _13;
else if( input >= 0x80 )  goto _7;
else                      goto _13;


    __quex_assert_no_passage();
_10:
    /* (124 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(124);
goto _18;


    __quex_assert_no_passage();
_11:
    /* (125 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(125);
if     ( input >= 0xC0 )  goto _13;
else if( input >= 0xA0 )  goto _8;
else if( input >= 0x80 )  goto _14;
else                      goto _13;


    __quex_assert_no_passage();
_12:
    /* (126 from 117)  */
    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(126);
if     ( input >= 0xC0 )  goto _13;
else if( input >= 0x90 )  goto _14;
else if( input >= 0x80 )  goto _7;
else                      goto _13;


    __quex_assert_no_passage();
_13:
    /* (127 from 122) (127 from 126) (127 from 128) (127 from 121) (127 from 125) (127 from 117) (127 from 123)  */

    ++(me->buffer._read_p);

    input = *(me->buffer._read_p);


    __quex_debug_state(127);
goto _19;

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_27:
    __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);

    __QUEX_IF_COUNT_COLUMNS((me->counter._column_number_at_end) = (size_t)1);

if( me->buffer._read_p != LexemeEnd ) goto _20;

goto _1;

_29:
    __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);

if( me->buffer._read_p != LexemeEnd ) goto _20;

goto _1;

_30:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);

if( me->buffer._read_p != LexemeEnd ) goto _20;

goto _1;

_28:
    __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

if( me->buffer._read_p != LexemeEnd ) goto _20;

goto _1;

_46:
    __quex_debug("* TERMINAL <BEYOND>\n");
    (me->buffer._read_p) = lexatom_begin_p;

goto _1;

if(0) {
    /* Avoid unreferenced labels. */
    goto _27;
    goto _29;
    goto _30;
    goto _28;
    goto _46;
}
_26: /* TERMINAL: BAD_LEXATOM */
;
_25: /* TERMINAL: FAILURE     */
goto _46;
_1:
     __quex_assert(me->buffer._read_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
    return;
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
_47:
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   undef self
#   undef QUEX_LABEL_STATE_ROUTER
#    if ! defined(QUEX_OPTION_COMPUTED_GOTOS)
     goto _47; /* in QUEX_GOTO_STATE       */
     goto _26; /* to BAD_LEXATOM           */
#    endif
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _46;
    goto _25;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
