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
#include <quex/code_base/analyzer/QuexMode>
#include <quex/code_base/analyzer/Analyser>


extern int  indentation[64];

class my_tester : public quex::QuexAnalyzerEngine {
public:
    my_tester();
    quex::Counter*   counter;
    quex::QuexMode   tester_mini_mode;
};

inline void 
mini_mode_on_indentation(quex::QuexAnalyzerEngine* x, int Indentation) 
{
    indentation[((my_tester*)x)->counter->base._line_number_at_end-1] = Indentation;
    printf("indentation = %i\n", Indentation);
}

my_tester::my_tester() 
{ 
    tester_mini_mode.on_indentation = mini_mode_on_indentation;
    __current_mode_p = &tester_mini_mode; 
}

#include <../CounterWithIndentation.i>
#include <../Counter.i>

#endif // __INCLUDE_GUARD_MY_TESTER_H__
