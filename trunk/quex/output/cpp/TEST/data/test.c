#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _73
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
 /* (94 from NONE) */
    input = *(me->buffer._input_p);

_32:
    character_begin_p = (me->buffer._input_p);



    __quex_debug("Init State\n");
__quex_debug_state(94);
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
                case 0x8: goto _17;
                case 0x9: goto _11;
                case 0xA: goto _19;

            }
        } else {
            if( input < 0x30 ) {
                goto _17;
            
} else if( input < 0x3A ) {
                goto _16;
            
} else if( input < 0x80 ) {
                goto _17;
            } else {
                goto _25;
            
}
        
}
    } else {
        if( input < 0xF1 ) {
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
                case 0xDF: goto _4;
                case 0xE0: goto _14;
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
                case 0xEF: goto _5;
                case 0xF0: goto _18;

            }
        } else {
            if( input == 0xF1 ) {
                goto _13;
            
} else if( input < 0xF4 ) {
                goto _15;
            
} else if( input < 0xF8 ) {
                goto _12;
            } else {
                goto _25;
            
}
        
}
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_30: /* (94 from 139) */
    goto _32;



    __quex_assert_no_passage();
_25: /* (DROP_OUT from 98) (DROP_OUT from 115) (DROP_OUT from 136) (DROP_OUT from 112) (DROP_OUT from 96) (DROP_OUT from 94) (DROP_OUT from 109) (DROP_OUT from 131) (DROP_OUT from 106) (DROP_OUT from 100) (DROP_OUT from 128) (DROP_OUT from 97) (DROP_OUT from 123) (DROP_OUT from 135) (DROP_OUT from 132) */
    me->buffer._input_p = me->buffer._lexeme_start_p + 1; 

goto _36;    goto _34;

_26: /* (DROP_OUT from 95) */
    goto _37;    goto _34;

_27: /* (DROP_OUT from 103) */
    goto _38;    goto _34;

_29: /* (DROP_OUT from 108) */
    goto _39;    goto _34;

_28: /* (DROP_OUT from 105) (DROP_OUT from 116) (DROP_OUT from 137) (DROP_OUT from 138) (DROP_OUT from 129) */
    goto _35;

_35:
    goto _40;    goto _34;

_34:

    __quex_debug("Drop-Out Catcher\n");

__quex_assert_no_passage();


    __quex_assert_no_passage();
_2: /* (128 from 123) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _41;

_41:

    __quex_debug_state(128);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _3;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_3: /* (129 from 128) (129 from 137) (129 from 116) */
    goto _43;

_43:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _42;

_42:

    __quex_debug_state(129);
    if( input >= 0xC0 ) {
        goto _28;
    
} else if( input >= 0x80 ) {
        goto _17;
    } else {
        goto _28;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_4: /* (131 from 98) (131 from 94) (131 from 132) */
    goto _45;

_45:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _44;

_44:

    __quex_debug_state(131);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _17;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_5: /* (132 from 94) (132 from 96) */
    goto _47;

_47:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _46;

_46:

    __quex_debug_state(132);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _4;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_6: /* (135 from 97) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _48;

_48:

    __quex_debug_state(135);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input == 0xBF ) {
        goto _7;
    
} else if( input >= 0x80 ) {
        goto _22;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_7: /* (136 from 135) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _49;

_49:

    __quex_debug_state(136);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input == 0xBF ) {
        goto _8;
    
} else if( input >= 0x80 ) {
        goto _23;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_8: /* (137 from 136) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _50;

_50:

    __quex_debug_state(137);
    if( input >= 0xC0 ) {
        goto _28;
    
} else if( input == 0xBF ) {
        goto _9;
    
} else if( input >= 0x80 ) {
        goto _3;
    } else {
        goto _28;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_9: /* (138 from 137) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _51;

_51:

    __quex_debug_state(138);
    if( input >= 0xBF ) {
        goto _28;
    
} else if( input >= 0x80 ) {
        goto _17;
    } else {
        goto _28;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_11: /* (95 from 94) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _52;

_52:

    __quex_debug_state(95);
goto _26;

    __quex_assert_no_passage();
_12: /* (96 from 112) (96 from 94) */
    goto _54;

_54:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _53;

_53:

    __quex_debug_state(96);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _5;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_13: /* (97 from 94) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _55;

_55:

    __quex_debug_state(97);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input == 0xBF ) {
        goto _6;
    
} else if( input >= 0x80 ) {
        goto _20;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_14: /* (98 from 94) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _56;

_56:

    __quex_debug_state(98);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0xA0 ) {
        goto _4;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_15: /* (100 from 94) (100 from 106) */
    goto _58;

_58:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _57;

_57:

    __quex_debug_state(100);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _24;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_16: /* (103 from 94) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _59;

_59:

    __quex_debug_state(103);
goto _27;

    __quex_assert_no_passage();
_17: /* (105 from 129) (105 from 138) (105 from 131) (105 from 94) */
    goto _61;

_61:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _60;

_60:

    __quex_debug_state(105);
goto _28;

    __quex_assert_no_passage();
_18: /* (106 from 94) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _62;

_62:

    __quex_debug_state(106);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x90 ) {
        goto _20;
    
} else if( input >= 0x88 ) {
        goto _15;
    
} else if( input >= 0x84 ) {
        goto _21;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_19: /* (108 from 94) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _63;

_63:

    __quex_debug_state(108);
goto _29;

    __quex_assert_no_passage();
_20: /* (109 from 97) (109 from 106) */
    goto _65;

_65:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _64;

_64:

    __quex_debug_state(109);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _22;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_21: /* (112 from 106) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _66;

_66:

    __quex_debug_state(112);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _12;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_22: /* (115 from 135) (115 from 109) */
    goto _68;

_68:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _67;

_67:

    __quex_debug_state(115);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _23;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_23: /* (116 from 115) (116 from 136) */
    goto _70;

_70:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _69;

_69:

    __quex_debug_state(116);
    if( input >= 0xC0 ) {
        goto _28;
    
} else if( input >= 0x80 ) {
        goto _3;
    } else {
        goto _28;
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_24: /* (123 from 100) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _71;

_71:

    __quex_debug_state(123);
    if( input >= 0xC0 ) {
        goto _25;
    
} else if( input >= 0x80 ) {
        goto _2;
    } else {
        goto _25;
    
}

__quex_assert_no_passage();

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_39: __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
    __QUEX_IF_COUNT_COLUMNS((me->counter._column_number_at_end) = (size_t)1;
);
if( me->buffer._input_p != LexemeEnd ) goto _30;
goto _1;
_37: __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);
if( me->buffer._input_p != LexemeEnd ) goto _30;
goto _1;
_38: __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);
if( me->buffer._input_p != LexemeEnd ) goto _30;
goto _1;
_40: __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _30;
goto _1;
_72: __quex_debug("* TERMINAL <BEYOND>\n");
    (me->buffer._input_p) = character_begin_p;
goto _1;
_36:
    goto _72;
_1:
     __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
    return;
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
_73:
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   undef self
#   undef QUEX_LABEL_STATE_ROUTER
#    if ! defined(QUEX_OPTION_COMPUTED_GOTOS)
     goto _73; /* in QUEX_GOTO_STATE       */
#    endif
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _72;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
