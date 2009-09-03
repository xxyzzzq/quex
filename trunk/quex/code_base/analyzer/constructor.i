/* -*- C++ -*- vim:set syntax=cpp:
 * NO INCLUDE GUARDS -- THIS FILE MIGHT BE INCLUDED TWICE FOR MULTIPLE
 *                      LEXICAL ANALYZERS
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_CONSTRUCTOR_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_CONSTRUCTOR_I__       */
#include <quex/code_base/buffer/Buffer.i>

#ifndef __QUEX_SETTING_PLAIN_C
namespace quex { 
#endif

    inline
    QUEX_CONSTRUCTOR(QUEX_TYPE_ANALYZER, _memory)(__QUEX_SETTING_THIS_POINTER
                                                  QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                                                  size_t               BufferMemorySize,
                                                  const char*          CharacterEncodingName /* = 0x0   */,
                                                  bool                 ByteOrderReversionF   /* = false */)
    {
        size_t  memory_size = BufferMemoryBegin != 0 ? BufferMemorySize 
                              :                        QUEX_SETTING_BUFFER_SIZE;

       __quex_assert(memory_size > 2);
       QUEX_TYPE_ANALYZER::__constructor_core((void*)0x0, CharacterEncodingName, ByteOrderReversionF,
                                 BufferMemoryBegin, memory_size);

    }

    inline
    QUEX_CONSTRUCTOR(QUEX_TYPE_ANALYZER, _file_name)(__QUEX_SETTING_THIS_POINTER
                                                     const std::string&  Filename, 
                                                     const char*         CharacterEncodingName /* = 0x0   */,
                                                     bool                ByteOrderReversionF   /* = false */)
    {
        // Buffer: Size = (see macro def.), Fallback = 10 Characters
        // prefer FILE* based buffers, because we can turn low-level buffering off.
        // ownership of FILE* id passed to the input strategy of the buffer
        std::FILE* fh = std::fopen(Filename.c_str(), "rb");
        if( fh == NULL ) QUEX_ERROR_EXIT("Error on attempt to open specified file.");
        setbuf(fh, 0);   // turn off system based buffering!
        //               // this is essential to profit from the quex buffer!
        __constructor_core(fh, CharacterEncodingName, ByteOrderReversionF);
        // Recall, that this thing as to be deleted/closed
        __file_handle_allocated_by_constructor = fh;
    }

    inline
    QUEX_CONSTRUCTOR(QUEX_TYPE_ANALYZER, _istream)(__QUEX_SETTING_THIS_POINTER
                                                   std::istream*   p_input_stream, 
                                                   const char*     CharacterEncodingName /* = 0x0   */,
                                                   bool            ByteOrderReversionF   /* = false */)
    {
        if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
        __constructor_core(p_input_stream, CharacterEncodingName, ByteOrderReversionF);
    }

    inline
    QUEX_CONSTRUCTOR(QUEX_TYPE_ANALYZER, _wistream)(__QUEX_SETTING_THIS_POINTER
                                                    std::wistream*  p_input_stream, 
                                                    const char*     CharacterEncodingName /* = 0x0   */,
                                                    bool            ByteOrderReversionF   /* = false */)
    {
        if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
        __constructor_core(p_input_stream, CharacterEncodingName, ByteOrderReversionF);
    }

#   if defined(__QUEX_OPTION_UNIT_TEST)
    template<class UnderlyingStreamT> inline
    QUEX_TYPE_ANALYZER::QUEX_TYPE_ANALYZER(quex::StrangeStream<UnderlyingStreamT>*  p_input_stream, 
                 const char*      CharacterEncodingName /* = 0x0   */,
                 bool             ByteOrderReversionF   /* = false */)
    {
        if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
        __constructor_core(p_input_stream, CharacterEncodingName, ByteOrderReversionF);
    }
#   endif

    inline
    QUEX_CONSTRUCTOR(QUEX_TYPE_ANALYZER, _FILE)(__QUEX_SETTING_THIS_POINTER
                                                std::FILE*   fh, 
                                                const char*  CharacterEncodingName /* = 0x0   */,
                                                bool         ByteOrderReversionF   /* = false */)
    {
        if( fh == NULL ) QUEX_ERROR_EXIT("Error: received NULL as a file handle.");
        setbuf(fh, 0);   // turn off system based buffering!
        //               // this is essential to profit from the quex buffer!
        __constructor_core(fh, CharacterEncodingName, ByteOrderReversionF);
    }


    inline
    QUEX_DESTRUCTOR(QUEX_TYPE_ANALYZER)(__QUEX_SETTING_THIS_POINTER) 
    {
        QuexAnalyser_destruct(this);
#       ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE 
        QuexTokenQueue_destruct(&_token_queue);
#       endif
        if( __file_handle_allocated_by_constructor != 0x0 ) {
            std::fclose(__file_handle_allocated_by_constructor); 
        }
    }

#ifndef __QUEX_SETTING_PLAIN_C
} // namespace quex
#endif
