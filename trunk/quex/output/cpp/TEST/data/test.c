#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;

    __QUEX_IF_COUNT_SHIFT_VALUES();

    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {
        if( (*(iterator)) < 0x3F ) {
            switch( (*(iterator)) ) {
                case 0x0: 
                case 0x1: 
                case 0x2: 
                case 0x3: 
                case 0x4: 
                case 0x5: 
                case 0x6: 
                case 0x7: 
                case 0x8: 
                case 0x9: __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                break;
                case 0xA: __QUEX_IF_COUNT_LINES_ADD((size_t)1);
            __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
                break;
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
                case 0x3B: __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                break;
                case 0x3C:                 break;
                case 0x3D: __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                break;
                case 0x3E: __QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);
                break;

            }
        } else {
            if( (*(iterator)) < 0x12001 ) {
                if( (*(iterator)) == 0x3F ) {
                    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);

                } else if( (*(iterator)) < 0x12000 ) {
                    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

                } else {
                    
                }
            } else {
                if( (*(iterator)) == 0x12001 ) {
                    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

                } else if( (*(iterator)) == 0x12002 ) {
                    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);

                } else if( (*(iterator)) == 0x12003 ) {
                    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);

                } else {
                    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

                }
            }
        }
    ++(iterator);
    }
    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
#   undef self
}
#endif /* __QUEX_OPTION_COUNTER */