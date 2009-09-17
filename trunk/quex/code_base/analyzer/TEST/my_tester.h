#ifndef __INCLUDE_GUARD_MY_TESTER_H__
#define __INCLUDE_GUARD_MY_TESTER_H__
#include <quex/code_base/compatibility/inttypes.h>

typedef uint8_t  QUEX_TYPE_CHARACTER;
typedef uint8_t* QUEX_TYPE_CHARACTER_POSITION; 

#include <quex/code_base/test_environment/default_configuration>
#include <cstdio>

struct my_tester;
#define QUEX_TYPE_ANALYZER my_tester
#define QUEX_TYPE_MODE_TAG QuexMode_tag
#define QUEX_TYPE_MODE     QuexMode
#include <quex/code_base/analyzer/Counter>


struct mini_mode {
    void on_indentation(my_tester* x, int Indentation);
};

extern int  indentation[64];

struct my_tester {
    quex::Counter*   counter;
    mini_mode        tester_mini_mode;
    mini_mode&       mode() { return tester_mini_mode; }
};

inline void 
mini_mode::on_indentation(my_tester* x, int Indentation) 
{
    indentation[x->counter->base._line_number_at_end-1] = Indentation;
    printf("indentation = %i\n", Indentation);
}

#include <../CounterWithIndentation.i>
#include <../Counter.i>

#endif // __INCLUDE_GUARD_MY_TESTER_H__
