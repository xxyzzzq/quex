#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    QUEX_TYPE_CHARACTER* iterator    = LexemeBegin;
#   if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)
    const QUEX_TYPE_CHARACTER* reference_p = LexemeBegin;
#   endif
__QUEX_IF_COUNT_COLUMNS(reference_p = iterator);
    __QUEX_IF_COUNT_SHIFT_VALUES();

    __quex_assert(LexemeBegin <= LexemeEnd);
    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {
        if( (*(iterator)) < 0x25 ) {
            switch( (*(iterator)) ) {
                case 0x0: 
                case 0x1: 
                case 0x2: 
                case 0x3: 
                case 0x4:                     ++(((iterator)));
                continue;
                case 0x5:             __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(((iterator) - reference_p)));
            __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
            __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4);
            __QUEX_IF_COUNT_COLUMNS(reference_p = (iterator) + 1);
                    ++(((iterator)));
                continue;
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
                case 0x24:                     ++(((iterator)));
                continue;

            }
        } else {
            if( (*(iterator)) == 0x25 ) {
                __QUEX_IF_COUNT_LINES_ADD((size_t)1);
            __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
            __QUEX_IF_COUNT_COLUMNS(reference_p = (iterator) + 1);
                    ++(((iterator)));
                continue;
            } else if( (*(iterator)) < 0x100 ) {
                                    ++(((iterator)));
                continue;
            } else {
                ++(((iterator)));
                continue;
            }
        }

    }
    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
__QUEX_IF_COUNT_COLUMNS_ADD((size_t)((iterator - reference_p)));
   return;
#  undef self
}
#endif /* __QUEX_OPTION_COUNTER */