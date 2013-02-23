#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;

    __QUEX_IF_COUNT_SHIFT_VALUES();

    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {
        if( (*iterator) < 0x4D ) {
            if( (*iterator) == 0x4C ) {
                
            } else if( (*iterator) >= 0x26 ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

            } else if( (*iterator) == 0x25 ) {
                __QUEX_IF_COUNT_LINES_ADD((size_t)1);
            __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);

            } else {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

            }
        } else {
            if( (*iterator) < 0x6E ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

            } else if( (*iterator) == 0x6E ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);

            } else if( (*iterator) == 0x6F ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);

            } else if( (*iterator) < 0x100 ) {
                __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

            } else {
                QUEX_ERROR_EXIT("Unexpected character for codec 'cp037'.\n"
                            "May be, codec transformation file from unicode contains errors.");
            }
        }
    ++iterator;
    }
    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
#   undef self
}
#endif /* __QUEX_OPTION_COUNTER */