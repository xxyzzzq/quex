#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    QUEX_TYPE_CHARACTER_POSITION   character_begin_p              = (QUEX_TYPE_CHARACTER_POSITION)0x0;
    (void)me;
    __QUEX_IF_COUNT_SHIFT_VALUES();
    /* Allow LexemeBegin == LexemeEnd (e.g. END_OF_STREAM)
     * => Caller does not need to check
     * BUT, if so quit immediately after 'shift values'. */
    __quex_assert(LexemeBegin <= LexemeEnd);
    if(LexemeBegin == LexemeEnd) return;
    me->buffer._input_p = LexemeBegin;
 /* (95 from NONE) */
    input = *(me->buffer._input_p);

_46:
    character_begin_p = (me->buffer._input_p);



    __quex_debug("Init State\n");
    __quex_debug_state(95);
    if( input < 0xC2 ) {
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
                case 0x8: goto _21;
                case 0x9: goto _19;
                case 0xA: goto _14;

            }
        } else {
            if( input < 0x30 ) {
                goto _21;
            
} else if( input < 0x3A ) {
                goto _20;
            
} else if( input < 0x80 ) {
                goto _21;
            } else {

            
}
        
}
    } else {
        switch( input ) {
            case 0xC2: 
            case 0xC3: 
            case 0xC4: 
            case 0xC5: 
            case 0xC6: 
            case 0xC7: 
            case 0xC8: 
            case 0xC9: 
            case 0xCA: 
            case 0xCB: 
            case 0xCC: 
            case 0xCD: 
            case 0xCE: 
            case 0xCF: 
            case 0xD0: 
            case 0xD1: 
            case 0xD2: 
            case 0xD3: 
            case 0xD4: 
            case 0xD5: 
            case 0xD6: 
            case 0xD7: 
            case 0xD8: 
            case 0xD9: 
            case 0xDA: 
            case 0xDB: 
            case 0xDC: 
            case 0xDD: 
            case 0xDE: 
            case 0xDF: goto _22;
            case 0xE0: goto _16;
            case 0xE1: 
            case 0xE2: 
            case 0xE3: 
            case 0xE4: 
            case 0xE5: 
            case 0xE6: 
            case 0xE7: 
            case 0xE8: 
            case 0xE9: 
            case 0xEA: 
            case 0xEB: 
            case 0xEC: 
            case 0xED: 
            case 0xEE: 
            case 0xEF: goto _3;
            case 0xF0: goto _17;
            case 0xF1: goto _15;
            case 0xF2: 
            case 0xF3: goto _18;
            case 0xF4: 
            case 0xF5: 
            case 0xF6: 
            case 0xF7: goto _2;

        }
    
}

    __quex_debug_drop_out(95);
goto _1;


    __quex_assert_no_passage();
_44: /* (95 from 140) */
    goto _46;



    __quex_assert_no_passage();
_2: /* (128 from 123) (128 from 95) */
    goto _49;

_49:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _48;

_48:

    __quex_debug_state(128);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _3;
    } else {

    
}

    __quex_debug_drop_out(128);
    goto _50;


    __quex_assert_no_passage();
_3: /* (129 from 128) (129 from 95) */
    goto _52;

_52:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _51;

_51:

    __quex_debug_state(129);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _22;
    } else {

    
}

    __quex_debug_drop_out(129);
    goto _50;


    __quex_assert_no_passage();
_4: /* (130 from 136) (130 from 120) */
    goto _54;

_54:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _53;

_53:

    __quex_debug_state(130);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _5;
    } else {

    
}

    __quex_debug_drop_out(130);
    goto _50;


    __quex_assert_no_passage();
_5: /* (131 from 130) (131 from 137) */
    goto _56;

_56:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _55;

_55:

    __quex_debug_state(131);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _6;
    } else {

    
}

    __quex_debug_drop_out(131);
    goto _57;


    __quex_assert_no_passage();
_6: /* (132 from 134) (132 from 131) (132 from 138) */
    goto _59;

_59:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _58;

_58:

    __quex_debug_state(132);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _21;
    } else {

    
}

    __quex_debug_drop_out(132);
    goto _57;


    __quex_assert_no_passage();
_7: /* (133 from 101) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _60;

_60:

    __quex_debug_state(133);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _8;
    } else {

    
}

    __quex_debug_drop_out(133);
    goto _50;


    __quex_assert_no_passage();
_8: /* (134 from 133) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _61;

_61:

    __quex_debug_state(134);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _6;
    } else {

    
}

    __quex_debug_drop_out(134);
    goto _50;


    __quex_assert_no_passage();
_9: /* (136 from 97) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _62;

_62:

    __quex_debug_state(136);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _4;
        case 0xBF: goto _10;

    }

    __quex_debug_drop_out(136);
    goto _50;


    __quex_assert_no_passage();
_10: /* (137 from 136) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _63;

_63:

    __quex_debug_state(137);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _5;
        case 0xBF: goto _11;

    }

    __quex_debug_drop_out(137);
    goto _50;


    __quex_assert_no_passage();
_11: /* (138 from 137) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _64;

_64:

    __quex_debug_state(138);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _6;
        case 0xBF: goto _12;

    }

    __quex_debug_drop_out(138);
    goto _57;


    __quex_assert_no_passage();
_12: /* (139 from 138) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _65;

_65:

    __quex_debug_state(139);
    if( input >= 0xBF ) {

    
} else if( input >= 0x80 ) {
        goto _21;
    } else {

    
}

    __quex_debug_drop_out(139);
    goto _57;


    __quex_assert_no_passage();
_14: /* (96 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _66;

_66:

    __quex_debug_state(96);
    __quex_debug_drop_out(96);
    goto _68;


    __quex_assert_no_passage();
_15: /* (97 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _69;

_69:

    __quex_debug_state(97);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _23;
        case 0xBF: goto _9;

    }

    __quex_debug_drop_out(97);
    goto _50;


    __quex_assert_no_passage();
_16: /* (98 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _70;

_70:

    __quex_debug_state(98);
    switch( input ) {
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _22;

    }

    __quex_debug_drop_out(98);
    goto _50;


    __quex_assert_no_passage();
_17: /* (99 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _71;

_71:

    __quex_debug_state(99);
    switch( input ) {
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: goto _24;
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: goto _18;
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _23;

    }

    __quex_debug_drop_out(99);
    goto _50;


    __quex_assert_no_passage();
_18: /* (101 from 95) (101 from 99) */
    goto _73;

_73:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _72;

_72:

    __quex_debug_state(101);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _7;
    } else {

    
}

    __quex_debug_drop_out(101);
    goto _50;


    __quex_assert_no_passage();
_19: /* (104 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _74;

_74:

    __quex_debug_state(104);
    __quex_debug_drop_out(104);
    goto _76;


    __quex_assert_no_passage();
_20: /* (105 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _77;

_77:

    __quex_debug_state(105);
    __quex_debug_drop_out(105);
    goto _79;


    __quex_assert_no_passage();
_21: /* (107 from 139) (107 from 95) (107 from 132) (107 from 109) */
    goto _81;

_81:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _80;

_80:

    __quex_debug_state(107);
    __quex_debug_drop_out(107);
    goto _57;


    __quex_assert_no_passage();
_22: /* (109 from 95) (109 from 129) (109 from 98) */
    goto _84;

_84:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _83;

_83:

    __quex_debug_state(109);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _21;
    } else {

    
}

    __quex_debug_drop_out(109);
    goto _50;


    __quex_assert_no_passage();
_23: /* (120 from 99) (120 from 97) */
    goto _86;

_86:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _85;

_85:

    __quex_debug_state(120);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _4;
    } else {

    
}

    __quex_debug_drop_out(120);
    goto _50;


    __quex_assert_no_passage();
_24: /* (123 from 99) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _87;

_87:

    __quex_debug_state(123);
    if( input >= 0xC0 ) {

    
} else if( input >= 0x80 ) {
        goto _2;
    } else {

    
}

    __quex_debug_drop_out(123);
    goto _50;

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_68: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _44;
goto _1;
_76: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);
if( me->buffer._input_p != LexemeEnd ) goto _44;
goto _1;
_79: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);
if( me->buffer._input_p != LexemeEnd ) goto _44;
goto _1;
_57: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _44;
goto _1;
_88: __quex_debug("* TERMINAL <BEYOND>\n");
    (me->buffer._input_p) = character_begin_p;
goto _1;
_50:
    goto _88;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _88;
}
#endif /* __QUEX_OPTION_COUNTER */
