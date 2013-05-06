#include <stdio.h>
#include <stdint.h>
#include <assert.h>

typedef DEF_CHARACTER_TYPE QUEX_TYPE_CHARACTER;

typedef struct {
    struct {
        size_t  _line_number_at_begin;
        size_t  _column_number_at_begin;
        size_t  _line_number_at_end;
        size_t  _column_number_at_end;
    } counter;
} QUEX_TYPE_ANALYZER;

#define __quex_debug(X) 
#define __quex_debug_state(X)
#define __quex_debug_drop_out(X)
#define __quex_assert(X)   assert(X)
#define __quex_assert_no_passage()    assert(0)
#define QUEX_ERROR_EXIT(X) assert(0)
#define QUEX_NAME(X)       quex_unit_test_ ## X

#define __QUEX_IF_COUNT_LINES(X)       X
#define __QUEX_IF_COUNT_LINES_ADD(X)   (me->counter._line_number_at_end += X)
#define __QUEX_IF_COUNT_COLUMNS(X)     X
#define __QUEX_IF_COUNT_COLUMNS_SET(X) (me->counter._column_number_at_end = X)
#define __QUEX_IF_COUNT_COLUMNS_ADD(X) (me->counter._column_number_at_end += X)
#define __QUEX_IF_COUNT_SHIFT_VALUES() \
        me->counter._line_number_at_begin = me->counter._line_number_at_end;    \
        me->counter._column_number_at_begin = me->counter._column_number_at_end;

#define QUEX_OPTION_COLUMN_NUMBER_COUNTING
#define QUEX_OPTION_LINE_NUMBER_COUNTING

void
DEF_COUNTER_FUNCTION(QUEX_TYPE_ANALYZER*  me, 
                     QUEX_TYPE_CHARACTER* LexemeBegin, 
                     QUEX_TYPE_CHARACTER* LexemeEnd);

