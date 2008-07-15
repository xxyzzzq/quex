// -*- C++ -*-  vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
//
// (C) 2008 Frank-Rene Schaefer
//
#if ! defined (__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS)
#   define QUEX_DEBUG_PRINT(Buffer, FormatStr, ...)       /* empty */
#   define QUEX_DEBUG_PRINT_INPUT(Buffer, Character)      /* empty */
#else
#   include<cstdio>
#   define __QUEX_PRINT_SOURCE_POSITION(Buffer)                       \
          std::fprintf(stderr, "%s:%i: @%08X \t", __FILE__, __LINE__, \
                       (int)((Buffer)->_input_p - (Buffer)->_memory._front));            

#   define QUEX_DEBUG_PRINT(Buffer, FormatStr, ...)   \
           __QUEX_PRINT_SOURCE_POSITION(Buffer)       \
           std::fprintf(stderr, FormatStr "\n", ##__VA_ARGS__)

#   define QUEX_DEBUG_PRINT_INPUT(Buffer, Character)                       \
           __QUEX_PRINT_SOURCE_POSITION(Buffer)                            \
             Character == '\n' ? std::fprintf(stderr, "input:    '\\n'\n") \
           : Character == '\t' ? std::fprintf(stderr, "input:    '\\t'\n") \
           :                     std::fprintf(stderr, "input:    (%x) '%c'\n", (char)Character, (int)Character) 
#endif

#ifdef __QUEX_OPTION_UNIT_TEST

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

#   define TEMPLATE_IN  template<class CharacterCarrierType> inline

    TEMPLATE_IN void 
    BufferFiller_show_brief_content(BUFFER_FILLER_TYPE* me) 
    {
        __quex_assert(me != 0x0);
        BUFFER_TYPE* buffer = me->client;
        __quex_assert(buffer != 0x0);
        std::printf("Begin of Buffer Character Index: %i\n", (int)buffer->_content_first_character_index);
        std::printf("End   of Buffer Character Index: %i\n", (int)me->tell_character_index(me));
        std::printf("_end_of_file_p (offset)  = %08X\n",     (int)(buffer->_end_of_file_p  - buffer->_memory._front));
        std::printf("_input_p (offset)        = %08X\n",     (int)(buffer->_current_p      - buffer->_memory._front));
        std::printf("_lexeme_start_p (offset) = %08X\n",     (int)(buffer->_lexeme_start_p - buffer->_memory._front));
    }

    TEMPLATE_IN void 
    Buffer_x_show_content(BUFFER_FILLER_TYPE* me) 
    {
        show_content(me);
        show_brief_content(me);
    }

    TEMPLATE_IN CharacterCarrierType
    __Buffer_get_border_char(const CharacterCarrierType* C) 
    {
        if     ( *C != QUEX_SETTING_BUFFER_LIMIT_CODE )                   return (CharacterCarrierType)'?'; 
        else if( C == _end_of_file_p )                                    return (CharacterCarrierType)']';
        else if( C == _buffer.front() && _character_index_at_front == 0 ) return (CharacterCarrierType)'[';
        else                                                              return (CharacterCarrierType)'|';
    }

    // Do not forget to include <iostream> before this header when doing those unit tests
    // which are using this function.
    TEMPLATE_IN void  
    BufferFiller_show_content(BUFFER_FILLER_TYPE* me) 
    {
        // NOTE: If the limiting char needs to be replaced temporarily by
        //       a terminating zero.
        // NOTE: This is a **simple** printing function for unit testing and debugging
        //       it is thought to print only ASCII characters (i.e. code points < 0xFF)
        int                    covered_char = 0xFFFF;
        CharacterCarrierType*  end_p = 0x0;
        CharacterCarrierType*  ContentSize  = Buffer_content_size(buffer);
        CharacterCarrierType*  ContentFront = Buffer_content_front(buffer);
        CharacterCarrierType*  BufferFront  = buffer->_memory._front;
        CharacterCarrierType*  BufferBack   = buffer->_memory._back;

        for(end_p = content_front(); end_p <= _buffer.back() ; ++end_p) {
            if( end_p == _end_of_file_p || *end_p == QUEX_SETTING_BUFFER_LIMIT_CODE ) { break; }
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
        tmp[content_size()+2] = get_border_char(BufferBack);
        tmp[1]                = get_border_char(BufferFront);
        tmp[0]                = '|';
        //
        tmp[_SHOW_current_fallback_n - 1 + 2] = ':';        
        tmp[buffer->_current_p - content_front() + 2] = 'C';
        if( buffer->_lexeme_start_p >= ContentFront && buffer->_lexeme_start_p <= BufferBack ) 
            tmp[(int)(buffer->_lexeme_start_p - ContentFront) + 2] = 'S';
        //
        if ( buffer->_current_p == ContentFront - 2 ) {
            std::cout << tmp << " <out>";
        } else {
            std::cout << tmp << " ";
            if( *buffer->_current_p == CLASS::BLC ) std::cout << "BLC";
            else                                    std::cout << "'" << *buffer->_current_p << "'";
        }
        // std::cout << " = 0x" << std::hex << int(*buffer->_current_p) << std::dec 
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

#undef TEMPLATE_IN
#undef CLASS

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex
#endif 

#endif // __QUEX_OPTION_UNIT_TEST

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
