// -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2008 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_

#include <iostream>
#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS)
#   define QUEX_DEBUG_PRINT(Buffer, FormatStr, ...)       /* empty */
#   define QUEX_DEBUG_PRINT_INPUT(Buffer, Character)      /* empty */
#else
#   include<cstdio>
#   define __QUEX_PRINT_SOURCE_POSITION(Buffer)                       \
          std::fprintf(stdout, "%s:%i: @%08X \t", __FILE__, __LINE__, \
                       (int)((Buffer)->_input_p - (Buffer)->_memory._front));            

#   define QUEX_DEBUG_PRINT(Buffer, FormatStr, ...)   \
           __QUEX_PRINT_SOURCE_POSITION(Buffer)       \
           std::fprintf(stdout, FormatStr "\n", ##__VA_ARGS__)

#   define QUEX_DEBUG_PRINT_INPUT(Buffer, Character)                       \
           __QUEX_PRINT_SOURCE_POSITION(Buffer)                            \
             Character == '\n' ? std::fprintf(stdout, "input:    '\\n'\n") \
           : Character == '\t' ? std::fprintf(stdout, "input:    '\\t'\n") \
           :                     std::fprintf(stdout, "input:    (%x) '%c'\n", (char)Character, (int)Character) 
#endif

#ifndef __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS 

#    define QUEX_DEBUG_PRINT_BUFFER_LOAD(Filler, Msg) /* empty */

#else

#    define QUEX_DEBUG_PRINT_BUFFER_LOAD(Filler, Msg)                   \
            QUEX_DEBUG_PRINT(Filler->client, "LOAD BUFFER " Msg); \
            BufferFiller_x_show_content(Filler); /* empty */

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif
    TEMPLATE_IN void BufferFiller_x_show_content(BUFFER_FILLER_TYPE* me); 
    TEMPLATE_IN void BufferFiller_show_brief_content(BUFFER_FILLER_TYPE* me);
    TEMPLATE_IN void BufferFiller_show_content(BUFFER_FILLER_TYPE* me); 

    TEMPLATE_IN void 
    BufferFiller_show_brief_content(BUFFER_FILLER_TYPE* me) 
    {
        __quex_assert(me != 0x0);
        BUFFER_TYPE* buffer = me->client;
        __quex_assert(buffer != 0x0);
        std::printf("Begin of Buffer Character Index: %i\n", (int)buffer->_content_first_character_index);
        std::printf("End   of Buffer Character Index: %i\n", (int)me->tell_character_index(me));
        std::printf("_end_of_file_p (offset)  = %08X\n",     (int)(buffer->_end_of_file_p  - buffer->_memory._front));
        std::printf("_input_p (offset)        = %08X\n",     (int)(buffer->_input_p      - buffer->_memory._front));
        std::printf("_lexeme_start_p (offset) = %08X\n",     (int)(buffer->_lexeme_start_p - buffer->_memory._front));
    }

    TEMPLATE_IN void 
    BufferFiller_x_show_content(BUFFER_FILLER_TYPE* me) 
    {
        BufferFiller_show_content(me);
        BufferFiller_show_brief_content(me);
    }

    TEMPLATE_IN CharacterCarrierType
    __BufferFiller_get_border_char(BUFFER_TYPE* buffer, const CharacterCarrierType* C) 
    {
        if     ( *C != QUEX_SETTING_BUFFER_LIMIT_CODE )   
            return (CharacterCarrierType)'?'; 
        else if( buffer->_end_of_file_p == C )       
            return (CharacterCarrierType)']';
        else if( buffer->_content_first_character_index == 0 && buffer->_memory._front == C )     
            return (CharacterCarrierType)'[';
        else
            return (CharacterCarrierType)'|';
    }

    // Do not forget to include <iostream> before this header when doing those unit tests
    // which are using this function.
    TEMPLATE_IN void  
    BufferFiller_show_content(BUFFER_FILLER_TYPE* me) 
    {
        __quex_assert(me != 0x0);
        BUFFER_TYPE* buffer = me->client;
        __quex_assert(buffer != 0x0);
        // NOTE: If the limiting char needs to be replaced temporarily by
        //       a terminating zero.
        // NOTE: This is a **simple** printing function for unit testing and debugging
        //       it is thought to print only ASCII characters (i.e. code points < 0xFF)
        int                    covered_char = 0xFFFF;
        CharacterCarrierType*  end_p = 0x0;
        const size_t           ContentSize  = QuexBuffer_content_size(buffer);
        CharacterCarrierType*  ContentFront = QuexBuffer_content_front(buffer);
        CharacterCarrierType*  BufferFront  = buffer->_memory._front;
        CharacterCarrierType*  BufferBack   = buffer->_memory._back;

        for(end_p = ContentFront; end_p <= BufferBack; ++end_p) {
            if( end_p == buffer->_end_of_file_p || *end_p == QUEX_SETTING_BUFFER_LIMIT_CODE ) { break; }
        }
        //_________________________________________________________________________________
        char tmp[ContentSize+4];
        // tmp[0]                  = outer border
        // tmp[1]                  = buffer limit
        // tmp[2...ContentSize+1] = ContentFront[0...ContentSize-1]
        // tmp[ContentSize+2]     = buffer limit
        // tmp[ContentSize+3]     = outer border
        // tmp[ContentSize+4]     = terminating zero
        for(size_t i=2; i<ContentSize + 2 ; ++i) tmp[i] = ' ';
        tmp[ContentSize+4] = '\0';
        tmp[ContentSize+3] = '|';
        tmp[ContentSize+2] = __BufferFiller_get_border_char(me->client, BufferBack);
        tmp[1]             = __BufferFiller_get_border_char(me->client, BufferFront);
        tmp[0]             = '|';
        //
        // tmp[_SHOW_current_fallback_n - 1 + 2] = ':';        
        tmp[buffer->_input_p - ContentFront + 2] = 'C';
        if( buffer->_lexeme_start_p >= ContentFront && buffer->_lexeme_start_p <= BufferBack ) 
            tmp[(int)(buffer->_lexeme_start_p - ContentFront) + 2] = 'S';
        //
        if ( buffer->_input_p == ContentFront - 2 ) {
            std::cout << tmp << " <out>";
        } else {
            std::cout << tmp << " ";
            if( *buffer->_input_p == QUEX_SETTING_BUFFER_LIMIT_CODE ) 
                std::cout << "BLC";
            else                                  
                std::cout << "'" << *buffer->_input_p << "'";
        }
        // std::cout << " = 0x" << std::hex << int(*buffer->_input_p) << std::dec 
        std::cout << std::endl;
        std::cout << "|" << __BufferFiller_get_border_char(me->client, BufferFront);
        for(CharacterCarrierType* iterator = ContentFront; iterator != end_p; ++iterator) {
            std::cout << *iterator;
        }
        std::cout << __BufferFiller_get_border_char(me->client, end_p);
        //
        const size_t L = (buffer->_end_of_file_p == 0x0) ? 0 : BufferBack - buffer->_end_of_file_p;
        for(size_t i=0; i < L; ++i) std::cout << "|";

        std::cout << "|\n";
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex
#endif 

#endif // __QUEX_OPTION_UNIT_TEST

#include <quex/code_base/temporary_macros_off>
#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_UNIT_TEST_I_
