#ifndef __INCLUDE_GUARD_MY_TESTER_H__
#define __INCLUDE_GUARD_MY_TESTER_H__
#include <quex/code_base/compatibility/inttypes.h>

typedef uint8_t  QUEX_CHARACTER_TYPE;
typedef uint8_t* QUEX_CHARACTER_POSITION; 

#ifdef QUEX_OPTION_ASSERTS
#   include <cassert>
#   define  __quex_assert(X)   assert(X)
#else
#   define  __quex_assert(X)   /*no assert*/
#endif

#include <iostream>

struct my_tester;
#define CLASS my_tester
#include <quex/code_base/template/Counter>


struct mini_mode {
    void on_indentation(my_tester* x, int Indentation);
};

extern mini_mode  tester_mini_mode;
extern int        indentation[64];

struct my_buffer {
    QUEX_CHARACTER_TYPE*  __the_end;
    QUEX_CHARACTER_TYPE*  content_begin() { return 0; }
    QUEX_CHARACTER_TYPE*  content_end()   { return __the_end; }
};

struct my_tester {
    my_buffer  __the_buffer;
    my_buffer* __buffer;
    quex::Counter*   _counter;

#ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    int  line_number_at_end() const  { return _counter->_line_number_at_end; }
#endif

    mini_mode   tester_mini_mode;

    mini_mode&  mode() { return tester_mini_mode; }

    my_tester() : 
        __buffer(&__the_buffer)
    {}
 
};

inline void 
mini_mode::on_indentation(my_tester* x, int Indentation) 
{
    indentation[x->line_number_at_end()-1] = Indentation;
    std::cout << "indentation = " << Indentation << std::endl;
}

#include <../CounterWithIndentation.i>
#include <../Counter.i>

#endif // __INCLUDE_GUARD_MY_TESTER_H__
