#ifndef __INCLUDE_GUARD_MY_TESTER_H__
#define __INCLUDE_GUARD_MY_TESTER_H__
#include <quex/code_base/compatibility/inttypes.h>

#define QUEX_TYPE_CHARACTER           uint8_t  

#include <cstdio>

struct my_tester;
#define  QUEX_TYPE_ANALYZER my_tester
#define  QUEX_TYPE_MODE_TAG QuexMode_tag  // divert 'attention' to outside definition
#define  QUEX_TYPE_MODE     QuexMode
#include <quex/code_base/test_environment/default_configuration>
#include <quex/code_base/analyzer/Counter>


typedef struct mini_mode_tag {
    void on_indentation(my_tester* x, int Indentation);
} mini_mode;

extern int  indentation[64];

struct my_tester {
    my_tester() : __current_mode_p(&tester_mini_mode) {}
    quex::Counter*   counter;
    mini_mode*       __current_mode_p;
    mini_mode        tester_mini_mode;
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
