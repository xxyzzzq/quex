/* -*- C++ -*-  vim: set syntax=cpp:
 *
 * (C) 2008 Frank-Rene Schaefer */
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_DEBUG_I_
#define __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_DEBUG_I_

#include <quex/code_base/definitions>

#if ! defined (__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS)
#   define QUEX_DEBUG_PRINT(Buffer, FormatStr, ...)       /* empty */
#   define QUEX_DEBUG_PRINT_INPUT(Buffer, Character)      /* empty */
#else
#   define __QUEX_PRINT_SOURCE_POSITION(Buffer)                       \
          __QUEX_STD_fprintf(stdout, "%s:%i: @%08X \t", __FILE__, __LINE__, \
                             (int)((Buffer)->_input_p - (Buffer)->_memory._front));            

#   define QUEX_DEBUG_PRINT(Buffer, FormatStr, ...)   \
           __QUEX_PRINT_SOURCE_POSITION(Buffer)       \
           __QUEX_STD_fprintf(stdout, FormatStr "\n", ##__VA_ARGS__)

#   define QUEX_DEBUG_PRINT_INPUT(Buffer, Character)                       \
           __QUEX_PRINT_SOURCE_POSITION(Buffer)                            \
             Character == '\n' ? __QUEX_STD_fprintf(stdout, "input:    '\\n'\n") \
           : Character == '\t' ? __QUEX_STD_fprintf(stdout, "input:    '\\t'\n") \
           :                     __QUEX_STD_fprintf(stdout, "input:    (%x) '%c'\n", (char)Character, (int)Character) 
#endif

#ifndef __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS 

#    define QUEX_DEBUG_PRINT_BUFFER_LOAD(Filler, Msg) /* empty */

#else

#    include <quex/code_base/definitions>
#    include <quex/code_base/buffer/Buffer>
#    include <quex/code_base/buffer/BufferFiller>

#    define QUEX_DEBUG_PRINT_BUFFER_LOAD(Filler, Msg)                   \
            QUEX_DEBUG_PRINT(Filler->client, "LOAD BUFFER " Msg); \
            BufferFiller_x_show_content(Filler); /* empty */

#    if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#    endif

    QUEX_INLINE_KEYWORD void BufferFiller_x_show_content(QuexBuffer* buffer); 
    QUEX_INLINE_KEYWORD void BufferFiller_show_brief_content(QuexBuffer* buffer);
    QUEX_INLINE_KEYWORD void BufferFiller_show_content(QuexBuffer* buffer); 

    QUEX_INLINE_KEYWORD void 
    BufferFiller_show_brief_content(QuexBuffer* buffer) 
    {
        __quex_assert(buffer != 0x0);
        QuexBufferFiller* me = buffer->filler;
        __quex_assert(me != 0x0);

        __QUEX_STD_printf("Begin of Buffer Character Index: %i\n", (int)buffer->_content_first_character_index);
        __QUEX_STD_printf("End   of Buffer Character Index: %i\n", (int)me->tell_character_index(me));
        __QUEX_STD_printf("_end_of_file_p (offset)  = %08X\n",     (int)(buffer->_end_of_file_p  - buffer->_memory._front));
        __QUEX_STD_printf("_input_p (offset)        = %08X\n",     (int)(buffer->_input_p      - buffer->_memory._front));
        __QUEX_STD_printf("_lexeme_start_p (offset) = %08X\n",     (int)(buffer->_lexeme_start_p - buffer->_memory._front));
    }

    QUEX_INLINE_KEYWORD void 
    BufferFiller_x_show_content(QuexBuffer* buffer) 
    {
        BufferFiller_show_content(buffer);
        BufferFiller_show_brief_content(buffer);
    }

    QUEX_INLINE_KEYWORD QUEX_CHARACTER_TYPE
    __BufferFiller_get_border_char(QuexBuffer* buffer, const QUEX_CHARACTER_TYPE* C) 
    {
        if     ( *C != QUEX_SETTING_BUFFER_LIMIT_CODE )   
            return (QUEX_CHARACTER_TYPE)'?'; 
        else if( buffer->_end_of_file_p == C )       
            return (QUEX_CHARACTER_TYPE)']';
        else if( buffer->_content_first_character_index == 0 && buffer->_memory._front == C )     
            return (QUEX_CHARACTER_TYPE)'[';
        else
            return (QUEX_CHARACTER_TYPE)'|';
    }

    void
    QuexBuffer_show_content(QuexBuffer* buffer)
    {
        size_t                i = 0;
        QUEX_CHARACTER_TYPE*  ContentFront = QuexBuffer_content_front(buffer);
        QUEX_CHARACTER_TYPE*  BufferFront  = buffer->_memory._front;
        QUEX_CHARACTER_TYPE*  BufferBack   = buffer->_memory._back;
        QUEX_CHARACTER_TYPE*  iterator = 0x0;
        QUEX_CHARACTER_TYPE*  end_p    = buffer->_end_of_file_p != 0x0 ? buffer->_end_of_file_p 
                                         :                               buffer->_memory._back + 1;

        __QUEX_STD_printf("|%c", __BufferFiller_get_border_char(buffer, BufferFront));
        for(iterator = ContentFront; iterator != end_p; ++iterator) {
            __QUEX_STD_printf("%c", *iterator);
        }
        __QUEX_STD_printf("%c", __BufferFiller_get_border_char(buffer, end_p));
        /**/
        const size_t L = (buffer->_end_of_file_p == 0x0) ? 0 : BufferBack - buffer->_end_of_file_p;
        for(i=0; i < L; ++i) __QUEX_STD_printf("|");

        __QUEX_STD_printf("|");
    }

    /* Do not forget to include <iostream> before this header when doing those unit tests*/
    /* which are using this function.*/
    QUEX_INLINE_KEYWORD void  
    BufferFiller_show_content(QuexBuffer* buffer) 
    {
        __quex_assert(buffer != 0x0);
        QuexBufferFiller*  me = buffer->filler;
        __quex_assert(me != 0x0);
        /* NOTE: If the limiting char needs to be replaced temporarily by
         *       a terminating zero.
         * NOTE: This is a **simple** printing function for unit testing and debugging
         *       it is thought to print only ASCII characters (i.e. code points < 0xFF)*/
        size_t                i = 0;
        int                   covered_char = 0xFFFF;
        QUEX_CHARACTER_TYPE*  end_p = 0x0;
        const size_t          ContentSize  = QuexBuffer_content_size(buffer);
        QUEX_CHARACTER_TYPE*  ContentFront = QuexBuffer_content_front(buffer);
        QUEX_CHARACTER_TYPE*  BufferFront  = buffer->_memory._front;
        QUEX_CHARACTER_TYPE*  BufferBack   = buffer->_memory._back;

        for(end_p = ContentFront; end_p <= BufferBack; ++end_p) {
            if( end_p == buffer->_end_of_file_p || *end_p == QUEX_SETTING_BUFFER_LIMIT_CODE ) { break; }
        }
        /*_________________________________________________________________________________*/
        char tmp[ContentSize+4];
        /* tmp[0]                  = outer border*/
        /* tmp[1]                  = buffer limit*/
        /* tmp[2...ContentSize+1] = ContentFront[0...ContentSize-1]*/
        /* tmp[ContentSize+2]     = buffer limit*/
        /* tmp[ContentSize+3]     = outer border*/
        /* tmp[ContentSize+4]     = terminating zero*/
        for(i=2; i<ContentSize + 2 ; ++i) tmp[i] = ' ';
        tmp[ContentSize+4] = '\0';
        tmp[ContentSize+3] = '|';
        tmp[ContentSize+2] = __BufferFiller_get_border_char(buffer, BufferBack);
        tmp[1]             = __BufferFiller_get_border_char(buffer, BufferFront);
        tmp[0]             = '|';
        /* tmp[_SHOW_current_fallback_n - 1 + 2] = ':';        */
        tmp[buffer->_input_p - ContentFront + 2] = 'C';
        if( buffer->_lexeme_start_p >= ContentFront && buffer->_lexeme_start_p <= BufferBack ) 
            tmp[(int)(buffer->_lexeme_start_p - ContentFront) + 2] = 'S';
        /**/
        if ( buffer->_input_p == ContentFront - 2 ) {
            __QUEX_STD_printf(tmp); __QUEX_STD_printf(" <out>");
        } else {
            __QUEX_STD_printf(" ");
            if( *buffer->_input_p == QUEX_SETTING_BUFFER_LIMIT_CODE ) 
                __QUEX_STD_printf("BLC");
            else                                  
                __QUEX_STD_printf("'%c'", (char)(*buffer->_input_p));
        }
        /* std::cout << " = 0x" << std::hex << int(*buffer->_input_p) << std::dec */
        __QUEX_STD_printf("\n");
        QuexBuffer_show_content(buffer);
    }



#   if ! defined(__QUEX_SETTING_PLAIN_C)
} /* namespace quex */
#   endif 

#   include <quex/code_base/buffer/Buffer.i>

#endif  /* __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS */

#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_DEBUG_I_ */
