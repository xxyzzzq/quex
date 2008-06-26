#ifndef __INCLUDE_GUARD_MY_TESTER_H__
#define __INCLUDE_GUARD_MY_TESTER_H__
#include <quex/code_base/compatibility/inttypes.h>

typedef uint8_t  QUEX_CHARACTER_TYPE;
typedef uint8_t* QUEX_CHARACTER_POSITION; 
typedef char     QUEX_CHARACTER_TYPE;

#ifdef QUEX_OPTION_ACTIVATE_ASSERTS
#   include <cassert>
#   define  __quex_assert(X)   assert(X)
#else
#   define  __quex_assert(X)   /*no assert*/
#endif

#include <iostream>

struct my_tester;


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

#ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    int  _line_number_at_begin;    // line where current pattern starts
    int  _line_number_at_end;     // line after current pattern
    int  line_number_at_begin() const { return _line_number_at_begin; }
    int  line_number_at_end() const  { return _line_number_at_end; }
#endif
#ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
    int  _column_number_at_begin;  // column where current pattern starts
    int  _column_number_at_end;   // column after current pattern
    int  column_number_at_begin() const { return _column_number_at_begin; }
    int  column_number_at_end() const  { return _column_number_at_end; }
#endif

    int  _indentation;
    bool _indentation_count_enabled_f;
    bool _indentation_event_enabled_f;

    mini_mode   tester_mini_mode;

    mini_mode&  mode() { return tester_mini_mode; }

    my_tester() : 
        __buffer(&__the_buffer),
        _line_number_at_begin(-1), _line_number_at_end(1), 
        _column_number_at_begin(-1), _column_number_at_end(1),
        _indentation(0), _indentation_count_enabled_f(true),
        _indentation_event_enabled_f(true)
    {}
 
	void  count(QUEX_CHARACTER_TYPE* Lexeme, const int LexemeLength);
	void  count_NoNewline(const int LexemeLength);
	void  count_FixNewlineN(QUEX_CHARACTER_TYPE* Lexeme, const int LexemeLength, 
				const int        LineNIncrement);

	void  count_indentation(QUEX_CHARACTER_TYPE* Lexeme, const int  LexemeLength);
	void  count_indentation_NoNewline(QUEX_CHARACTER_TYPE* Lexeme, const int LexemeLength);
	void  count_indentation_NoNewline_NeverStartOnWhitespace(const int ColumnNIncrement);
	void  count_indentation_NoNewline_ContainsOnlySpace(const int ColumnNIncrement);

	void  __count_indentation_aux(QUEX_CHARACTER_TYPE* start_consideration_it,
	             		      QUEX_CHARACTER_TYPE* Begin,
	             		      QUEX_CHARACTER_TYPE* End, 
	             		      const bool       LicenseToCountF);

	void  __count_whitespace_to_first_non_whitespace(QUEX_CHARACTER_TYPE* start_consideration, 
	             				         QUEX_CHARACTER_TYPE* Begin,
	             				         QUEX_CHARACTER_TYPE* End,
	             				         const bool       LicenseToCountF);
	void  __count_assert_consistency();

	void  __count_shift_end_values_to_start_values();

	void  __count_newline_n_backwards(QUEX_CHARACTER_TYPE* it,
					  QUEX_CHARACTER_TYPE* Begin);

	QUEX_CHARACTER_TYPE* __count_chars_to_newline_backwards(QUEX_CHARACTER_TYPE* Begin,
							        QUEX_CHARACTER_TYPE* End,
							        const int        LexemeLength,
							        const bool       LicenseToIncrementLineCountF=false);

};

inline void 
mini_mode::on_indentation(my_tester* x, int Indentation) 
{
    indentation[x->line_number_at_end()-1] = Indentation;
    std::cout << "indentation = " << Indentation << std::endl;
}

#define CLASS my_tester
#include <../count_line_column-with-indentation.i>
#include <../count_line_column.i>

#endif // __INCLUDE_GUARD_MY_TESTER_H__
