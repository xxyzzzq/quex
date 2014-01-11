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
_3: /* (11 from 19) (11 from NONE) */
    input = *(me->buffer._input_p);



    __quex_debug("Init State\n");
    __quex_debug_state(11);
    if( input < 0xD800 ) {
        if( input >= 0xB ) {
            goto _7;
        
} else if( input == 0xA ) {
            goto _5;
        
} else if( input == 0x9 ) {
            goto _4;
        } else {
            goto _7;
        
}
    } else {
        if( input < 0xDC00 ) {
            goto _6;
        
} else if( input < 0xE000 ) {

        
} else if( input < 0x10000 ) {
            goto _7;
        } else {

        
}
    
}

    __quex_debug_drop_out(11);
    __quex_debug("Character counting terminated.\n");
    goto _2;


    __quex_assert_no_passage();


    __quex_assert_no_passage();
_4: /* (16 from 11) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _12;

_12:

    __quex_debug_state(16);
    __quex_debug_drop_out(16);
goto _14;

    __quex_assert_no_passage();
_5: /* (17 from 11) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _15;

_15:

    __quex_debug_state(17);
    __quex_debug_drop_out(17);
goto _17;

    __quex_assert_no_passage();
_6: /* (12 from 11) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _18;

_18:

    __quex_debug_state(12);
    if( input >= 0xE000 ) {

    
} else if( input >= 0xDC00 ) {
        goto _7;
    } else {

    
}

    __quex_debug_drop_out(12);
goto _2;

    __quex_assert_no_passage();
_7: /* (15 from 12) (15 from 11) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _19;

_19:

    __quex_debug_state(15);
    __quex_debug_drop_out(15);
goto _21;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_21: __quex_debug("* TERMINAL [0000, 0008] [000B, D7FF] [E000, 10FFFF] \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p == LexemeEnd ) goto _2;;
goto _3;
_14: __quex_debug("* TERMINAL [0009] \n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4);
if( me->buffer._input_p == LexemeEnd ) goto _1;;
goto _3;
_17: __quex_debug("* TERMINAL [000A] \n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
if( me->buffer._input_p == LexemeEnd ) goto _1;;
goto _3;
_2: __quex_debug("* TERMINAL -- Exit --\n");
goto _1;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
}
#endif /* __QUEX_OPTION_COUNTER */
