#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    QUEX_TYPE_CHARACTER* iterator    = LexemeBegin;
    __QUEX_IF_COUNT_SHIFT_VALUES();

    __quex_assert(LexemeBegin <= LexemeEnd);
    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {
        if( (*(iterator)) < 0x4D ) {
            if( (*(iterator)) == 0x4C ) {
                                    ++(((iterator)));
                continue;
            } else if( (*(iterator)) >= 0x26 ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                    ++(((iterator)));
                continue;
            } else if( (*(iterator)) == 0x25 ) {
                __QUEX_IF_COUNT_LINES_ADD((size_t)1);
            __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);
                    ++(((iterator)));
                continue;
            } else {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                    ++(((iterator)));
                continue;
            }
        } else {
            if( (*(iterator)) < 0x6E ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                    ++(((iterator)));
                continue;
            } else if( (*(iterator)) == 0x6E ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);
                    ++(((iterator)));
                continue;
            } else if( (*(iterator)) == 0x6F ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);
                    ++(((iterator)));
                continue;
            } else if( (*(iterator)) < 0x100 ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);
                    ++(((iterator)));
                continue;
            } else {
                ++(((iterator)));
                continue;
            }
        }

    }
    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
   return;
#  undef self
}
#endif /* __QUEX_OPTION_COUNTER */