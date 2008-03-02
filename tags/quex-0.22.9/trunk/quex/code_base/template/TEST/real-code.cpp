#include <my_tester.h>
#include <cassert>
#line 1 "../count_line_column-with-indentation.i"
// -*- C++ -*-   :vim set syntax=cpp:

#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT	
// NOTE: Quex is pretty intelligent in choosing the right function
//       to count line and column numbers. If, for example, a pattern
//       does not contain newlines, then it simply adds the LexemeLength
//       to the column number and does not do anything to the line number.
//       Before touching anything in this code, first look at the generated
//       code. The author of these lines considers it rather difficult to
//       find better implementations of these functions in the framework
//       of the generated engine.  <fschaef 07y6m30d>
//
// NOTE: Those functions are not responsible for setting the begin to the
//       last end, such as _line_number_at_begin = _line_number_at_end.
//       This has to happen outside these functions.

void    
my_tester::count_indentation(QUEX_LEXEME_CHARACTER_TYPE* Lexeme,
                                        const int            LexemeLength)
// PURPOSE:
//   Adapts the column number and the line number according to the newlines
//   and letters of the last line occuring in the lexeme.
//
////////////////////////////////////////////////////////////////////////////////
{
    //  NOTE: Indentation counting is only active between newline and the
    //        first non-whitespace character in a line. Use a variable
    //        to indicate the activation of newline.
    //  
    //  DEF: End_it   = pointer to first letter behind lexeme
    //       Begin_it = pointer to first letter of lexeme
    //  
    //  (1) last character of Lexeme == newline?
    //      yes => indentation_counting = ON
    //             indentation   = 0
    //             line_number_at_end   += number of newlines in Lexeme
    //             column_number_at_end  = 0           
    //      END
    //  
    //  (2) find last newline in Lexeme -> start_consideration_it
    //  
    //      (2.1) no newline in lexeme?
    //      yes => indentation_counting == ON ?
    //             no => perform normal line number and column number counting
    //                   (we are not in between newline and the first non-whitespace 
    //                    character of a line).
    //                   END
    //             yes => start_consideration_it = Begin_it
    //  
    //  (3) Count
    //  
    //      indentation  += number of whitespace between start_consideration 
    //                      and first non-whitespace character
    //      did non-whitespace character arrive?
    //         yes => indentation_counting = OFF
    //  
    //      column_number_at_end  = End_it - start_consideration_it
    //      line_number_at_end   += number of newlines from: Begin_it to: start_consideration_it
    //  
    assert( LexemeLength != 0 );
    QUEX_CHARACTER_TYPE* Begin = (QUEX_CHARACTER_TYPE*)Lexeme;
    QUEX_CHARACTER_TYPE* End   = Begin + LexemeLength;  
    QUEX_CHARACTER_TYPE* Last  = End - 1;                
    QUEX_CHARACTER_TYPE* it    = Last;

    assert(Begin >= __buffer->content_begin());
    assert(Begin < __buffer->content_end()-1); // LexemeLength >= 1
    assert(End <= __buffer->content_end());    // End > Lexeme follows from LexemeL > 0
    assert(Begin < End);                       // LexemeLength >= 1


    // (1) Last character == newline ? _______________________________________________
    //
    if( *Last == '\n' ) {
        _indentation = 0;
        _indentation_count_enabled_f = true;
#       ifndef  QUEX_NO_SUPPORT_FOR_LINE_NUMBER_COUNTING
        ++_line_number_at_end;
        __count_newline_n_backwards(it, Begin);
#       endif
#       ifndef  QUEX_NO_SUPPORT_FOR_COLUMN_NUMBER_COUNTING
        _column_number_at_end = 1;            // next lexeme starts at _column_number_at_end + 1
#       endif
        return;
    }

    // (2) Find last newline in lexeme _______________________________________________
    //
    QUEX_CHARACTER_TYPE* start_consideration_it = 0x0;
    it = Last;
    while( it != Begin ) {
        // recall assert: no lexeme with len(Lexeme) == 0
        --it;
        if( *it == '\n' ) { 		
            // NOTE: according to the test in (1) it is not possible
            //       that *it == "\n" and it == Last 
            //       => there is always an iterator behind 'it'
            //          if *it == "\n". The incrementation does
            //          not need a check;
            start_consideration_it = it;
            ++start_consideration_it;  // point to first character after newline
            _indentation = 0;
            _indentation_count_enabled_f = true;
#           ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
            _column_number_at_end = 1;
#           endif
            break; 
        }	    
    }
    // (2.1) no newline in lexeme?
    if( start_consideration_it == 0x0 ) {
        if( _indentation_count_enabled_f == false ) {
            // count increment without consideration of indentations
            // no newline => no line number increment
            //               no column number overflow / restart at '1'
            // no indentation enabled => no indentation increment
#           ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
            _column_number_at_end += LexemeLength;
#           endif
            return;
        }
        // There was no newline, but the flag '_indentation_count_enabled_f'
        // tells us that before this pattern there was only whitespace after 
        // newline. Let us add the whitespace at the beginning of this pattern
        // to the _indentation.
        start_consideration_it = Begin;
    }
    // At this point:
    //   -- either there was no newline in the pattern, but the indentation
    //      count was active (see case above).
    //   -- or there was a newline in the pattern, so above it is set
    //      '_indentation_count_enabled_f = true'.
    assert( _indentation_count_enabled_f == true );

    // (3) Count _____________________________________________________________________
    //
    // -- whitespace from: start_consideration to first non-whitespace
    //    (indentation count is disabled if non-whitespace arrives)
    //
    __count_whitespace_to_first_non_whitespace(start_consideration_it, Begin, End, 
                                               /* LicenseToIncrementLineCountF = */ true);

    __count_assert_consistency();
}


void    
my_tester::count_indentation_NoNewline(QUEX_LEXEME_CHARACTER_TYPE* Lexeme,
                                                  const int           LexemeLength)
{
    // NOTE: For an explanation of the algorithm, see the function:
    //       count_line_column_n_increment_w_indent(...)
    //
    assert( LexemeLength != 0 );
    QUEX_CHARACTER_TYPE* Begin = (QUEX_CHARACTER_TYPE*)Lexeme;
    QUEX_CHARACTER_TYPE* End   = (QUEX_CHARACTER_TYPE*)(Lexeme + LexemeLength);  

    assert(Begin >= __buffer->content_begin());
    assert(Begin < __buffer->content_end()-1); // LexemeLength >= 1
    assert(End <= __buffer->content_end());    // End > Lexeme follows from LexemeL > 0
    assert(Begin < End);                       // LexemeLength >= 1

    // (1) Last character == newline ? _______________________________________________
    //     [impossible, lexeme does never contain a newline]
    // (2) Find last newline in lexeme _______________________________________________
    //     [cannot be found]
    // (2.1) no newline in lexeme? [yes]
    if( _indentation_count_enabled_f == false ) {
        // count increment without consideration of indentations
        // no newline => no line number increment
        //               no column number overflow / restart at '1'
        // no indentation enabled => no indentation increment
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _column_number_at_end += LexemeLength;
#       endif
        return;
    }
    
    // The flag '_indentation_count_enabled_f' tells us that before this
    // pattern there was only whitespace after newline. Let us add the
    // whitespace at the beginning of this pattern to the _indentation.
    __count_whitespace_to_first_non_whitespace(Begin, Begin, End, /* LicenseToIncrementLineCountF = */ false);

    __count_assert_consistency();
}

void  
my_tester::count_indentation_NoNewline_NeverStartOnWhitespace(const int ColumnNIncrement) 
{
    assert(ColumnNIncrement > 0);  // lexeme length >= 1
#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_end += ColumnNIncrement;
#   endif
    if( _indentation_count_enabled_f ) {
        _indentation_count_enabled_f = false; 
        mode().on_indentation(this, _indentation);
    }
    __count_assert_consistency();
}

void  
my_tester::count_indentation_NoNewline_ContainsOnlySpace(const int ColumnNIncrement) 
{
    assert(ColumnNIncrement > 0);  // lexeme length >= 1
#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_end += ColumnNIncrement;
#   endif
    if( _indentation_count_enabled_f ) _indentation += ColumnNIncrement;

    __count_assert_consistency();
}

void
my_tester::__count_whitespace_to_first_non_whitespace(QUEX_CHARACTER_TYPE* start_consideration_it, 
                                                                 QUEX_CHARACTER_TYPE* Begin,
                                                                 QUEX_CHARACTER_TYPE* End,
                                                                 const bool              LicenseToCountF)
// NOTE: The 'license' flag shall enable the compiler to **delete** the line number counting
//       from the following function or implement it unconditionally, since the decision
//       is based on a constant (either true or false) -- once the function has been inlined.   
{
    // (3) Count _____________________________________________________________________
    //
    // -- whitespace from: start_consideration to first non-whitespace
    //    (indentation count is disabled if non-whitespace arrives)
    QUEX_CHARACTER_TYPE* it = start_consideration_it;
    do { 
        if( *it != ' ' ) { 
            _indentation_count_enabled_f = false;
            _indentation += it - start_consideration_it;
            // Line and column number need to be counted before the indentation handler
            // is called. this way it has to correct information.
            __count_indentation_aux(start_consideration_it, Begin, End, LicenseToCountF);
            // indentation event enabled:
            //   yes -> call indentation event handler
            //   no  -> enable event for the next time.
            //          indentation events can only be disabled for one coming event.
            if( _indentation_event_enabled_f ) 
                mode().on_indentation(this, _indentation);
            else
                // event was disabled this time, enable it for the next time.
                _indentation_event_enabled_f = true;

            return;
        }
        ++it; 		    
    } while ( it != End );

    // no non-whitespace until end of lexeme, thus only increment the indentation
    _indentation += it - start_consideration_it;
    __count_indentation_aux(start_consideration_it, Begin, End, LicenseToCountF);
}

void
my_tester::__count_indentation_aux(QUEX_CHARACTER_TYPE* start_consideration_it,
                                              QUEX_CHARACTER_TYPE* Begin,
                                              QUEX_CHARACTER_TYPE* End, 
                                              const bool          LicenseToCountF)
{
    // when inlined, this is a condition on a constant => deleted by compiler.
    if( LicenseToCountF == false ) return;

#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    __count_newline_n_backwards(start_consideration_it, Begin);
#   endif	    
#   ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_end += End - start_consideration_it;
#   endif

}

#endif // __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT	
#include <my_tester.h>
#include <cassert>
#line 1 "../count_line_column.i"
// -*- C++ -*-   :vim set syntax=cpp:

// NOTE: Quex is pretty intelligent in choosing the right function
//       to count line and column numbers. If, for example, a pattern
//       does not contain newlines, then it simply adds the LexemeLength
//       to the column number and does not do anything to the line number.
//       Before touching anything in this code, first look at the generated
//       code. The author of these lines considers it rather difficult to
//       find better implementations of these functions in the framework
//       of the generated engine.  <fschaef 07y6m30d>
//
// NOTE: Those functions are not responsible for setting the begin to the
//       last end, such as _line_number_at_begin = _line_number_at_end.
//       This has to happen outside these functions.

void 
my_tester::__count_assert_consistency()
{
    assert(_line_number_at_begin   <= _line_number_at_end);
    // if line number remained the same, then the column number **must** have increased.
    // there is not pattern of a length less than 1
    assert(_line_number_at_begin != _line_number_at_end || 
           _column_number_at_begin <  _column_number_at_end);
}

void             
my_tester::__count_shift_end_values_to_start_values() 
{
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    _line_number_at_begin   = _line_number_at_end;
#   endif
#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_begin = _column_number_at_end;
#   endif
}


void    
my_tester::count(QUEX_LEXEME_CHARACTER_TYPE* Lexeme,
                            const int        LexemeLength)
// PURPOSE:
//   Adapts the column number and the line number according to the newlines
//   and letters of the last line occuring in the lexeme.
//
// NOTE: Providing LexemeLength may spare a subtraction (End - Lexeme) in case 
//       there is no newline in the lexeme (see below).
//
////////////////////////////////////////////////////////////////////////////////
{
    assert( LexemeLength > 0 );
#if ! defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) && \
    ! defined(QUEX_OPTION_LINE_NUMBER_COUNTING)    
    return;
#else
    QUEX_CHARACTER_TYPE* Begin = (QUEX_CHARACTER_TYPE*)Lexeme;
    QUEX_CHARACTER_TYPE* it = __count_chars_to_newline_backwards(Begin, Begin + LexemeLength, LexemeLength,
                                                             /* LicenseToIncrementLineCountF = */ true);

#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    // The last function may have digested a newline (*it == '\n'), but then it 
    // would have increased the _line_number_at_end.
    __count_newline_n_backwards(it, Begin);
#   endif

    __count_assert_consistency();
#endif
}

void  
my_tester::count_NoNewline(const int LexemeLength) 
{
    assert( LexemeLength > 0 );

#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_end += LexemeLength;
#   endif

    __count_assert_consistency();
}

void  
my_tester::count_FixNewlineN(QUEX_LEXEME_CHARACTER_TYPE* Lexeme,
                                        const int           LexemeLength, 
                                        const int           LineNIncrement) 
{
    assert( LexemeLength > 0 );
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    _line_number_at_end += LineNIncrement;
#   endif

#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    __count_chars_to_newline_backwards((QUEX_CHARACTER_TYPE*)Lexeme, 
                                       (QUEX_CHARACTER_TYPE*)(Lexeme + LexemeLength), 
                                       LexemeLength,
                                       /* LicenseToIncrementLineCountF = */ false);
#   endif

    __count_assert_consistency();
}


void
my_tester::__count_newline_n_backwards(QUEX_CHARACTER_TYPE* it,
                                                  QUEX_CHARACTER_TYPE* Begin)
// NOTE: If *it == '\n' this function does **not** count it. The user must
//       have increased the _line_number_at_end by hisself. This happens
//       for performance reasons.
{
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    // investigate remaining part of the lexeme, i.e. before the last newline
    // (recall the lexeme is traced from the rear)
    while( it != Begin ) {
        --it;
        if( *it == '\n' ) ++_line_number_at_end; 
    }         
#   endif
}

QUEX_CHARACTER_TYPE*
my_tester::__count_chars_to_newline_backwards(QUEX_CHARACTER_TYPE* Begin,
                                                         QUEX_CHARACTER_TYPE* End,
                                                         const int        LexemeLength,
                                                         const bool       LicenseToIncrementLineCountF /*=false*/)
// RETURNS: Pointer to the first newline or the beginning of the lexeme.
//
// This function increases _line_number_at_end if a newline occurs and 
// LicenseToIncrementLineCountF = true.
//
// NOTE: The 'license' flag shall enable the compiler to **delete** the line number counting
//       from the following function or implemented unconditionally, since the decision
//       is based, then on a condition of a constant (either true or false) -- once the 
//       function has been inlined.   
//
// NOTE: Quex writes a call to this function only, if there **is** a potential
//       newline in the lexeme. Otherwise, it adds the fixed pattern length
//       or the LexemeLength directly.
{
#if ! defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) && \
    ! defined(QUEX_OPTION_LINE_NUMBER_COUNTING)    
    return;
#else
    assert(Begin >= __buffer->content_begin());
    assert(Begin < __buffer->content_end()-1); // LexemeLength >= 1
    assert(End <= __buffer->content_end());    // End > Lexeme follows from LexemeL > 0
    assert(Begin < End);                       // LexemeLength >= 1

    // loop from [End] to [Begin]:
    //
    //        [Begin]xxxxxxxxxxxxxxxxxxxxxxxxxx\n
    //     \n
    //     \n xxxxxxxxxxxxxxxxxxxxxxxx[End]
    //               <---------
    //
    QUEX_CHARACTER_TYPE* it = End - 1;
    for(; *it != '\n' ; --it) {
        if( it == Begin ) {
            // -- in case NO newline occurs, the column index is to be INCREASED 
            //    by the length of the string -1, since counting starts at zero
            // -- _column_number_at_begin = _column_number_at_end - LexemeLength (just take the old one)
            _column_number_at_end += LexemeLength;
            return it;
        }
    }
    // -- in case that newline occurs, the column index is equal to
    //    the number of letters from newline to end of string
    _column_number_at_end = End - it;
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    if( LicenseToIncrementLineCountF ) ++_line_number_at_end;
#   endif
# endif
    return it;
}
