#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;
    QUEX_TYPE_CHARACTER        input       = (QUEX_TYPE_CHARACTER)0;

    __QUEX_IF_COUNT_SHIFT_VALUES();

    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {
        input = *iterator;
        __quex_debug("Init State\n");
        __quex_debug_state(84);
        if( input < 0x40 ) {
            switch( input ) {
                case 0x0: 
                case 0x1: 
                case 0x2: 
                case 0x3: 
                case 0x4: 
                case 0x5: 
                case 0x6: 
                case 0x7: 
                case 0x8: 
                case 0x9: goto _87;
                case 0xA: goto _86;
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
                case 0x2F: 
                case 0x30: 
                case 0x31: 
                case 0x32: 
                case 0x33: 
                case 0x34: 
                case 0x35: 
                case 0x36: 
                case 0x37: 
                case 0x38: 
                case 0x39: 
                case 0x3A: 
                case 0x3B: goto _87;
                case 0x3C: goto _85;
                case 0x3D: goto _87;
                case 0x3E: goto _93;
                case 0x3F: goto _90;

            }
        } else {
            if( input < 0xD809 ) {
                if( input < 0xD800 ) {
                    goto _87;
                } else if( input < 0xD808 ) {
                    goto _88;
                } else {
                    goto _94;
                }
            } else {
                if( input < 0xDC00 ) {
                    goto _88;
                } else if( input < 0xE000 ) {

                } else if( input < 0x10000 ) {
                    goto _87;
                } else {

                }
            }
        }
        __quex_debug_drop_out(84);
        
        goto _97; /* TERMINAL_FAILURE */

        __quex_assert_no_passage();
_87: /* (87 from 88) (87 from 84) (87 from 94) */

        ++iterator;
        __quex_debug_state(87);
        __quex_debug_drop_out(87);
        goto TERMINAL_16;

        __quex_assert_no_passage();
_85: /* (85 from 94) (85 from 84) */

        ++iterator;
        __quex_debug_state(85);
        __quex_debug_drop_out(85);
        goto TERMINAL_18;

        __quex_assert_no_passage();
_90: /* (90 from 94) (90 from 84) */

        ++iterator;
        __quex_debug_state(90);
        __quex_debug_drop_out(90);
        goto TERMINAL_20;

        __quex_assert_no_passage();
_93: /* (93 from 94) (93 from 84) */

        ++iterator;
        __quex_debug_state(93);
        __quex_debug_drop_out(93);
        goto TERMINAL_19;

        __quex_assert_no_passage();
_86: /* (86 from 84) */

        ++iterator;
        __quex_debug_state(86);
        __quex_debug_drop_out(86);
        goto TERMINAL_17;

        __quex_assert_no_passage();
_88: /* (88 from 84) */

        ++iterator;
        input = *iterator;
        __quex_debug_state(88);
        if( input >= 0xE000 ) {

        } else if( input >= 0xDC00 ) {
            goto _87;
        } else {

        }
        __quex_debug_drop_out(88);
        
        goto _97; /* TERMINAL_FAILURE */

        __quex_assert_no_passage();
_94: /* (94 from 84) */

        ++iterator;
        input = *iterator;
        __quex_debug_state(94);
        if( input < 0xDC02 ) {
            switch( input ) {
                case 0xDC00: goto _85;
                case 0xDC01: goto _87;

            }
        } else {
            if( input == 0xDC02 ) {
                goto _93;
            } else if( input == 0xDC03 ) {
                goto _90;
            } else if( input < 0xE000 ) {
                goto _87;
            } else {

            }
        }
        __quex_debug_drop_out(94);
        
        goto _97; /* TERMINAL_FAILURE */
TERMINAL_16:
        __quex_debug("* terminal 16:   \n");
        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

        continue;

TERMINAL_17:
        __quex_debug("* terminal 17:   \n");
        __QUEX_IF_COUNT_LINES_ADD((size_t)1);
        __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);

        continue;

TERMINAL_18:
        __quex_debug("* terminal 18:   \n");
        
        continue;

TERMINAL_19:
        __quex_debug("* terminal 19:   \n");
        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);

        continue;

TERMINAL_20:
        __quex_debug("* terminal 20:   \n");
        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);

        continue;

_97: /* TERMINAL: FAILURE */
        QUEX_ERROR_EXIT("State machine failed.");
    }
    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
#   undef self
}
#endif /* __QUEX_OPTION_COUNTER */