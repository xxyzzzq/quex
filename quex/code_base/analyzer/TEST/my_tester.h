#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
#define __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
#include <quex/code_base/compatibility/inttypes.h>

#define QUEX_TYPE_CHARACTER           uint8_t  

#include <cstdio>

struct my_tester;
#define  QUEX_TYPE_ANALYZER my_tester
#include <quex/code_base/analyzer/configuration/default>
#include <quex/code_base/analyzer/counter/LineColumn>
#include <quex/code_base/analyzer/Mode>
#include <quex/code_base/analyzer/AnalyzerData>


extern int  indentation[64];

class my_tester : public QUEX_NAME(AnalyzerData) {
public:
    my_tester();
    quex::CounterLineColumn*   counter;
    quex::QuexMode             tester_mini_mode;
};

inline void 
mini_mode_on_indentation(quex::QuexAnalyzerData* x, int Indentation) 
{
    indentation[((my_tester*)x)->counter->base._line_number_at_end-1] = Indentation;
    printf("indentation = %i\n", Indentation);
}

my_tester::my_tester() 
{ 
    tester_mini_mode.on_indentation = mini_mode_on_indentation;
    engine.__current_mode_p = &tester_mini_mode; 
}

#include <../counter/LineColumnIndentation.i>
#include <../counter/LineColumn.i>

#endif // __QUEX_INCLUDE_GUARD__ANALYZER__TEST__MY_TESTER_H
