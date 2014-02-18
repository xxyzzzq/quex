#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    QUEX_TYPE_CHARACTER_POSITION   reference_p                    = (QUEX_TYPE_CHARACTER_POSITION)0x0;
    (void)me;
    __QUEX_IF_COUNT_SHIFT_VALUES();
    /* Allow LexemeBegin == LexemeEnd (e.g. END_OF_STREAM)
     * => Caller does not need to check
     * BUT, if so quit immediately after 'shift values'. */
    __quex_assert(LexemeBegin <= LexemeEnd);
    if(LexemeBegin == LexemeEnd) return;
    me->buffer._input_p = LexemeBegin;
 /* (2 from NONE) */
    input = *(me->buffer._input_p);

_8:

    __quex_debug("Init State\n");
    __quex_debug_state(2);
    if( input < 0x25 ) {
        switch( input ) {
            case 0x0: 
            case 0x1: 
            case 0x2: 
            case 0x3: 
            case 0x4: goto _5;
            case 0x5: goto _4;
            case 0x6: 
            case 0x7: 
            case 0x8: 
            case 0x9: 
            case 0xA: 
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
            case 0x24: goto _5;

        }
    } else {
        if( input == 0x25 ) {
            goto _3;
        
} else if( input < 0x100 ) {
            goto _5;
        } else {

        
}
    
}

    __quex_debug_drop_out(2);
goto _1;


    __quex_assert_no_passage();
_7: /* (2 from 7) */
    goto _8;



    __quex_assert_no_passage();
_3: /* (3 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _10;

_10:

    __quex_debug_state(3);
    __quex_debug_drop_out(3);
goto _12;

    __quex_assert_no_passage();
_4: /* (4 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _13;

_13:

    __quex_debug_state(4);
    __quex_debug_drop_out(4);
goto _15;

    __quex_assert_no_passage();
_5: /* (5 from 2) */
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    goto _16;

_16:

    __quex_debug_state(5);
    __quex_debug_drop_out(5);
goto _18;
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */
_12: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_LINES_ADD((size_t)1);
__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
__QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);
if( me->buffer._input_p != LexemeEnd ) goto _7;;
goto _1;
_15: __quex_debug("* TERMINAL \n");
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)((me->buffer._input_p - reference_p)));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
__QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4);
__QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);
if( me->buffer._input_p != LexemeEnd ) goto _7;;
goto _1;
_18: __quex_debug("* TERMINAL \n");
if( me->buffer._input_p != LexemeEnd ) goto _7;;
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)((me->buffer._input_p - reference_p)));
goto _1;
_19: __quex_debug("* TERMINAL <BEYOND>\n");
    --(me->buffer._input_p);
goto _1;
_1:
    __quex_assert(me->buffer._input_p == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
}
#endif /* __QUEX_OPTION_COUNTER */
