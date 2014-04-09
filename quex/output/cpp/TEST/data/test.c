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
 /* (23 from NONE) */
    input = *(me->buffer._input_p);

_13:
    character_begin_p = (me->buffer._input_p);



    __quex_debug("Init State\n");
    __quex_debug_state(23);
    if( input < 0x3A ) {
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
            case 0xA: goto _3;
            case 0xB: 
            case 0xC: 
            case 0xD: 
            case 0xE: 
            case 0xF: 
            case 0x10: 
            case 0x11: 
            case 0x12: 
            case 0x13: 
            case 0x14: 
            case 0x15: 
            case 0x16: 
            case 0x17: 
            case 0x18: 
            case 0x19: 
            case 0x1A: 
            case 0x1B: 
            case 0x1C: 
            case 0x1D: 
            case 0x1E: 
            case 0x1F: 
            case 0x20: 
            case 0x21: 
            case 0x22: 
            case 0x23: 
            case 0x24: 
            case 0x25: 
            case 0x26: 
            case 0x27: 
            case 0x28: 
            case 0x29: 
            case 0x2A: 
            case 0x2B: 
            case 0x2C: 
            case 0x2D: 
            case 0x2E: 
            case 0x2F: goto _7;
            case 0x30: 
            case 0x31: 
            case 0x32: 
            case 0x33: 
            case 0x34: 
            case 0x35: 
            case 0x36: 
            case 0x37: 
            case 0x38: 
            case 0x39: goto _6;

        }
    } else {
        if( input < 0xD800 ) {
            goto _7;
        
} else if( input < 0xDC00 ) {
            goto _4;
        
} else if( input < 0xE000 ) {

        
} else if( input < 0x10000 ) {
            goto _7;
        } else {

        
}
    
}

    __quex_debug_drop_out(23);
goto _1;


    __quex_assert_no_passage();
_11: /* (23 from 32) */
    goto _13;



    __quex_assert_no_passage();
_3: /* (24 from 23) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _15;

_15:

    __quex_debug_state(24);
    __quex_debug_drop_out(24);
goto _17;

    __quex_assert_no_passage();
_4: /* (25 from 23) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _18;

_18:

    __quex_debug_state(25);
    if( input >= 0xE000 ) {

    
} else if( input >= 0xDC00 ) {
        goto _7;
    } else {

    
}

    __quex_debug_drop_out(25);
goto _19;

    __quex_assert_no_passage();
_5: /* (27 from 23) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _20;

_20:

    __quex_debug_state(27);
    __quex_debug_drop_out(27);
goto _22;

    __quex_assert_no_passage();
_6: /* (28 from 23) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _23;

_23:

    __quex_debug_state(28);
    __quex_debug_drop_out(28);
goto _25;

    __quex_assert_no_passage();
_7: /* (29 from 23) (29 from 25) */
    goto _27;

_27:
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _26;

_26:

    __quex_debug_state(29);
    __quex_debug_drop_out(29);
goto _29;

    __quex_assert_no_passage();
 /* (30 from 23) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _30;

_30:

    __quex_debug_state(30);
    __quex_debug_drop_out(30);
goto _32;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_17: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _11;
goto _1;
_22: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end -= 1);
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4 + 1);
if( me->buffer._input_p != LexemeEnd ) goto _11;
goto _1;
_25: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)10);
if( me->buffer._input_p != LexemeEnd ) goto _11;
goto _1;
_29: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
if( me->buffer._input_p != LexemeEnd ) goto _11;
goto _1;
_32: __quex_debug("* TERMINAL <BEYOND>\n");
    (me->buffer._input_p) = character_begin_p;
goto _1;
_19:
    goto _32;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
    /* Avoid compiler warning: Unused label for 'TERMINAL <BEYOND>' */
    goto _32;
}
#endif /* __QUEX_OPTION_COUNTER */
