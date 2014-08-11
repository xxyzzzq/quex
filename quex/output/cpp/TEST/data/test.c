#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
/*  'QUEX_GOTO_STATE' requires 'QUEX_LABEL_STATE_ROUTER' */
#   define QUEX_LABEL_STATE_ROUTER _69
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
 /* (81 from NONE) */
    input = *(me->buffer._input_p);

_30:
    character_begin_p = (me->buffer._input_p);



    __quex_debug("Init State\n");
__quex_debug_state(81);
    if( input < 0xE0 ) {
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
                case 0x8: goto _7;
                case 0x9: goto _5;
                case 0xA: goto _4;

            }
        } else {
if( input < 0x80 ) {
                goto _7;

} else if( input < 0xC2 ) {
                goto _24;
} else {
                goto _10;

}
        
}
    } else {
        if( input < 0xF1 ) {
            switch( input ) {
                case 0xE0: goto _8;
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
                case 0xEF: goto _9;
                case 0xF0: goto _6;

            }
        } else {
if( input == 0xF1 ) {
                goto _11;

} else if( input < 0xF4 ) {
                goto _3;

} else if( input < 0xF8 ) {
                goto _12;
} else {
                goto _24;

}
        
}
    
}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_28: /* (81 from 125) */
    goto _30;



    __quex_assert_no_passage();
_24: /* (DROP_OUT from 87) (DROP_OUT from 90) (DROP_OUT from 102) (DROP_OUT from 105) (DROP_OUT from 81) (DROP_OUT from 96) (DROP_OUT from 91) (DROP_OUT from 103) (DROP_OUT from 85) (DROP_OUT from 88) (DROP_OUT from 82) (DROP_OUT from 95) (DROP_OUT from 110) (DROP_OUT from 89) (DROP_OUT from 104) */
    me->buffer._input_p = me->buffer._lexeme_start_p + 1; 

goto _34;    goto _32;

_25: /* (DROP_OUT from 83) */
    goto _35;    goto _32;

_26: /* (DROP_OUT from 84) */
    goto _36;    goto _32;

_27: /* (DROP_OUT from 109) (DROP_OUT from 106) (DROP_OUT from 97) (DROP_OUT from 86) (DROP_OUT from 107) */
    goto _33;

_33:
    goto _37;    goto _32;

_32:

    __quex_debug("Drop-Out Catcher\n");

__quex_assert_no_passage();


    __quex_assert_no_passage();
_3: /* (82 from 85) (82 from 81) */
    goto _39;

_39:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _38;

_38:

    __quex_debug_state(82);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _13;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_4: /* (83 from 81) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _40;

_40:

    __quex_debug_state(83);
goto _25;

    __quex_assert_no_passage();
_5: /* (84 from 81) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _41;

_41:

    __quex_debug_state(84);
goto _26;

    __quex_assert_no_passage();
_6: /* (85 from 81) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _42;

_42:

    __quex_debug_state(85);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x90 ) {
        goto _16;

} else if( input >= 0x88 ) {
        goto _3;

} else if( input >= 0x84 ) {
        goto _23;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_7: /* (86 from 81) (86 from 97) (86 from 109) (86 from 89) */
    goto _44;

_44:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _43;

_43:

    __quex_debug_state(86);
goto _27;

    __quex_assert_no_passage();
_8: /* (87 from 81) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _45;

_45:

    __quex_debug_state(87);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0xA0 ) {
        goto _10;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_9: /* (88 from 91) (88 from 81) */
    goto _47;

_47:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _46;

_46:

    __quex_debug_state(88);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _10;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_10: /* (89 from 88) (89 from 81) (89 from 87) */
    goto _49;

_49:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _48;

_48:

    __quex_debug_state(89);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _7;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_11: /* (90 from 81) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _50;

_50:

    __quex_debug_state(90);
if( input >= 0xC0 ) {
        goto _24;

} else if( input == 0xBF ) {
        goto _17;

} else if( input >= 0x80 ) {
        goto _16;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_12: /* (91 from 81) (91 from 110) */
    goto _52;

_52:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _51;

_51:

    __quex_debug_state(91);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _9;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_13: /* (95 from 82) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _53;

_53:

    __quex_debug_state(95);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _14;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_14: /* (96 from 95) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _54;

_54:

    __quex_debug_state(96);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _15;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_15: /* (97 from 96) (97 from 106) (97 from 107) */
    goto _56;

_56:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _55;

_55:

    __quex_debug_state(97);
if( input >= 0xC0 ) {
        goto _27;

} else if( input >= 0x80 ) {
        goto _7;
} else {
        goto _27;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_16: /* (102 from 90) (102 from 85) */
    goto _58;

_58:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _57;

_57:

    __quex_debug_state(102);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _18;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_17: /* (103 from 90) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _59;

_59:

    __quex_debug_state(103);
if( input >= 0xC0 ) {
        goto _24;

} else if( input == 0xBF ) {
        goto _19;

} else if( input >= 0x80 ) {
        goto _18;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_18: /* (104 from 103) (104 from 102) */
    goto _61;

_61:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _60;

_60:

    __quex_debug_state(104);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _21;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_19: /* (105 from 103) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _62;

_62:

    __quex_debug_state(105);
if( input >= 0xC0 ) {
        goto _24;

} else if( input == 0xBF ) {
        goto _20;

} else if( input >= 0x80 ) {
        goto _21;
} else {
        goto _24;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_20: /* (106 from 105) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _63;

_63:

    __quex_debug_state(106);
if( input >= 0xC0 ) {
        goto _27;

} else if( input == 0xBF ) {
        goto _22;

} else if( input >= 0x80 ) {
        goto _15;
} else {
        goto _27;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_21: /* (107 from 104) (107 from 105) */
    goto _65;

_65:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _64;

_64:

    __quex_debug_state(107);
if( input >= 0xC0 ) {
        goto _27;

} else if( input >= 0x80 ) {
        goto _15;
} else {
        goto _27;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_22: /* (109 from 106) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _66;

_66:

    __quex_debug_state(109);
if( input >= 0xBF ) {
        goto _27;

} else if( input >= 0x80 ) {
        goto _7;
} else {
        goto _27;

}

__quex_assert_no_passage();


    __quex_assert_no_passage();
_23: /* (110 from 85) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _67;

_67:

    __quex_debug_state(110);
if( input >= 0xC0 ) {
        goto _24;

} else if( input >= 0x80 ) {
        goto _12;
} else {
        goto _24;

}

__quex_assert_no_passage();

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_35: __quex_debug("* TERMINAL LINE\n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
    __QUEX_IF_COUNT_COLUMNS((me->counter._column_number_at_end) = (size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _28;
goto _1;
_36: __quex_debug("* TERMINAL GRID\n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);
if( me->buffer._input_p != LexemeEnd ) goto _28;
goto _1;
_37: __quex_debug("* TERMINAL COLUMN\n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _28;
goto _1;
_68: __quex_debug("* TERMINAL <BEYOND>\n");
    (me->buffer._input_p) = character_begin_p;
goto _1;
_34:
    goto _68;
_1:
     __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
    return;
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
_69:
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   undef self
#   undef QUEX_LABEL_STATE_ROUTER
#    if ! defined(QUEX_OPTION_COMPUTED_GOTOS)
     goto _69; /* in QUEX_GOTO_STATE       */
#    endif
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _68;
    (void)target_state_index;
    (void)target_state_else_index;
}
#endif /* __QUEX_OPTION_COUNTER */
