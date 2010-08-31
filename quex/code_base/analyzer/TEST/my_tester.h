#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
#define __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
#include <quex/code_base/compatibility/inttypes.h>

#define QUEX_TYPE_CHARACTER           uint8_t  

#include <cstdio>

struct my_tester;

namespace quex {
    typedef struct {} Token;
    typedef int       CounterLineColumnIndentation;
}
#define  QUEX_TYPE_ANALYZER my_tester
#include <quex/code_base/test_environment/TestAnalyzer-configuration>
namespace quex {
    typedef void      (*QUEX_NAME(AnalyzerFunctionP))(struct my_tester*);
}
#include <quex/code_base/analyzer/counter/LineColumn>
#include <quex/code_base/analyzer/Mode>
#include <quex/code_base/test_environment/TestAnalyzer>
#include <quex/code_base/analyzer/member/basic>


extern int  indentation[64];

class my_tester : public quex::QUEX_NAME(TestAnalyzer) {
public:
    my_tester();
    quex::QUEX_NAME(CounterLineColumn)*   counter;
    quex::QUEX_NAME(Mode)                 tester_mini_mode;
};

inline void 
mini_mode_on_indentation(my_tester* x, size_t Indentation) 
{
    indentation[((my_tester*)x)->counter->base._line_number_at_end-1] = Indentation;
    printf("indentation = %i\n", Indentation);
}

my_tester::my_tester() 
{ 
    /* tester_mini_mode.on_indentation = mini_mode_on_indentation; */
    __current_mode_p = &tester_mini_mode; 
}

#include <../counter/LineColumnIndentation.i>
#include <../counter/LineColumn.i>
#include <../../MemoryManager.i>

#endif // __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
