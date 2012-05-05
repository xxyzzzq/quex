#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
#define __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
#include <quex/code_base/compatibility/stdint.h>

#define QUEX_TYPE_CHARACTER           uint8_t  

#include <cstdio>

struct my_tester;

namespace quex {
    //typedef struct {} Token;
    typedef int       CounterLineColumnIndentation;
}
#include <quex/code_base/test_environment/TestAnalyzer>
//#include <quex/code_base/analyzer/Counter>
//#include <quex/code_base/analyzer/Mode>
#undef   QUEX_TYPE_ANALYZER
#undef   QUEX_TYPE0_ANALYZER
#define  QUEX_TYPE_ANALYZER  my_tester
#define  QUEX_TYPE0_ANALYZER my_tester
#include <quex/code_base/analyzer/member/basic>


extern int  indentation[64];

class my_tester : 
    public quex::TestAnalyzer {
public:
    my_tester();
    quex::QUEX_NAME(Counter)   counter;
    quex::QUEX_NAME(Mode)      tester_mini_mode;
};

inline void 
mini_mode_on_indentation(my_tester* x, size_t Indentation) 
{
    indentation[((my_tester*)x)->counter._line_number_at_end-1] = Indentation;
    printf("indentation = %i\n", Indentation);
}

my_tester::my_tester() 
{ 
    /* tester_mini_mode.on_indentation = mini_mode_on_indentation; */
    __current_mode_p = &tester_mini_mode; 
}

#include <../Counter.i>
#include <../../MemoryManager.i>

#endif // __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
