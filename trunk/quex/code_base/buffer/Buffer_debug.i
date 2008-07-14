// -*- C++ -*-  vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
//
// (C) 2008 Frank-Rene Schaefer
//
#if ! defined (__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS)
#   define QUEX_DEBUG_PRINT(FormatStr, ...)       /* empty */
#   define QUEX_DEBUG_PRINT_INPUT(Character)      /* empty */
#else
#   define __QUEX_PRINT_SOURCE_POSITION()                             \
          std::fprintf(stderr, "%s:%i: @%08X \t", __FILE__, __LINE__, \
                       (int)(me->input_p - me->buffer_begin));            

#   define QUEX_DEBUG_PRINT(FormatStr, ...)   \
           __QUEX_PRINT_SOURCE_POSITION()   \
           std::fprintf(stderr, FormatStr, ##__VA_ARGS__)

#   define QUEX_DEBUG_PRINT_INPUT(Character)                               \
           __QUEX_PRINT_SOURCE_POSITION()                                  \
             Character == '\n' ? std::fprintf(stderr, "input:    '\\n'\n") \
           : Character == '\t' ? std::fprintf(stderr, "input:    '\\t'\n") \
           :                     std::fprintf(stderr, "input:    (%x) '%c'\n", (char)Character, (int)Character) 
#endif

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#   define TEMPLATE_IN  template<class InputStrategy> inline
#   define CLASS        Buffer<InputStrategy>   

#ifdef __QUEX_OPTION_UNIT_TEST
#if 0
    TEMPLATE_IN void 
    CLASS::show_brief_content() 
    {
        std::cout << "start-pos:  " << _character_index_at_front << std::endl;
        std::cout << "end-pos:    " << _character_index_at_front + content_size() << std::endl;
        const long  Pos = _input->tell_character_index();
        std::cout << "stream-pos: " << Pos << std::endl;
        std::cout << "EOF = "       << bool(_end_of_file_p);
        std::cout << ", BOF = "     << bool(_character_index_at_front == 0) << std::endl;
        std::cout << "current_p (offset)    = " << _current_p      - content_front() << std::endl;
        std::cout << "lexeme start (offset) = " << _lexeme_start_p - content_front() << std::endl;
    }

    TEMPLATE_IN void CLASS::x_show_content() 
    {
        show_content();
        show_brief_content();
    }

    TEMPLATE_IN typename CLASS::character_type  CLASS::get_border_char(const character_type* C) 
    {
        if     ( *C != CLASS::BLC )                                       return '?'; 
        else if( C == _end_of_file_p )                                    return ']';
        else if( C == _buffer.front() && _character_index_at_front == 0 ) return '[';
        return '|';
    }

    // Do not forget to include <iostream> before this header when doing those unit tests
    // which are using this function.
    TEMPLATE_IN void  CLASS::show_content() 
    {
        // NOTE: if the limiting char needs to be replaced temporarily by
        //       a terminating zero.
        // NOTE: this is a **simple** printing function for unit testing and debugging
        //       it is thought to print only ASCII characters (i.e. code points < 0xFF)
        int              covered_char = 0xFFFF;
        character_type*  end_p = 0x0;

        for(end_p = content_front(); end_p <= _buffer.back() ; ++end_p) {
            if( end_p == _end_of_file_p || *end_p == CLASS::BLC ) { break; }
        }
        //_________________________________________________________________________________
        char tmp[content_size()+4];
        // tmp[0]                  = outer border
        // tmp[1]                  = buffer limit
        // tmp[2...content_size()+1] = content_front()[0...content_size()-1]
        // tmp[content_size()+2]     = buffer limit
        // tmp[content_size()+3]     = outer border
        // tmp[content_size()+4]     = terminating zero
        for(size_t i=2; i<content_size() + 2 ; ++i) tmp[i] = ' ';
        tmp[content_size()+4] = '\0';
        tmp[content_size()+3] = '|';
        tmp[content_size()+2] = get_border_char(_buffer.back());
        tmp[1]                = get_border_char(_buffer.front());
        tmp[0]                = '|';
        //
        tmp[_SHOW_current_fallback_n - 1 + 2] = ':';        
        tmp[_current_p - content_front() + 2] = 'C';
        if( _lexeme_start_p >= content_front() && _lexeme_start_p <= _buffer.back() ) 
            tmp[(int)(_lexeme_start_p - content_front()) + 2] = 'S';
        //
        if ( _current_p == content_front() - 2 ) {
            std::cout << tmp << " <out>";
        } else {
            std::cout << tmp << " ";
            if( *_current_p == CLASS::BLC ) std::cout << "BLC";
            else                            std::cout << "'" << *_current_p << "'";
        }
        // std::cout << " = 0x" << std::hex << int(*_current_p) << std::dec 
        std::cout << std::endl;
        std::cout << "|" << get_border_char(_buffer.front());
        for(character_type* iterator = content_front(); iterator != end_p; ++iterator) {
            std::cout << *iterator;
        }
        std::cout << get_border_char(end_p);
        //
        const size_t L = (_end_of_file_p == 0x0) ? 0 : _buffer.back() - _end_of_file_p;
        for(size_t i=0; i < L; ++i) std::cout << "|";

        std::cout << "|\n";
    }
#endif
#endif // __QUEX_OPTION_UNIT_TEST

#undef TEMPLATE_IN
#undef CLASS
} // namespace quex
#endif // ! defined (__QUEX_SETTING_PLAIN_C)

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
