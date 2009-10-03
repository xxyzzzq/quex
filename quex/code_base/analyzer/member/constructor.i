/* -*- C++ -*- vim:set syntax=cpp:
 * NO INCLUDE GUARDS -- THIS FILE MIGHT BE INCLUDED TWICE FOR MULTIPLE
 *                      LEXICAL ANALYZERS
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_CONSTRUCTOR_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_CONSTRUCTOR_I__       */
#include <quex/code_base/buffer/Buffer.i>

QUEX_NAMESPACE_COMPONENTS_OPEN

QUEX_INLINE
QUEX_CONSTRUCTOR(ANALYZER, _memory)(__QUEX_SETTING_THIS_POINTER
                                    QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                                    size_t               BufferMemorySize,
                                    const char*          CharacterEncodingName /* = 0x0   */,
                                    bool                 ByteOrderReversionF   /* = false */)
{
    size_t  memory_size = BufferMemoryBegin != 0 ? BufferMemorySize 
                          :                        QUEX_SETTING_BUFFER_SIZE;

   __quex_assert(memory_size > 2);
   QUEX_FIX(ANALYZER, __constructor_core)(this, (void*)0x0, CharacterEncodingName, ByteOrderReversionF,
                                          BufferMemoryBegin, memory_size);

}

QUEX_INLINE
QUEX_CONSTRUCTOR(ANALYZER, _file_name)(__QUEX_SETTING_THIS_POINTER
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
    QUEX_FIX(ANALYZER, __constructor_core)(this, fh, CharacterEncodingName, ByteOrderReversionF, 0x0, 0);
    // Recall, that this thing as to be deleted/closed
    __file_handle_allocated_by_constructor = fh;
}

QUEX_INLINE
QUEX_CONSTRUCTOR(ANALYZER, _istream)(__QUEX_SETTING_THIS_POINTER
                                     std::istream*   p_input_stream, 
                                     const char*     CharacterEncodingName /* = 0x0   */,
                                     bool            ByteOrderReversionF   /* = false */)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_FIX(ANALYZER, __constructor_core)(this, p_input_stream, 
                                           CharacterEncodingName, 
                                           ByteOrderReversionF, 
                                           0x0, 0);
}


#if defined(__QUEX_OPTION_WCHAR_T)
QUEX_INLINE
QUEX_CONSTRUCTOR(ANALYZER, _wistream)(__QUEX_SETTING_THIS_POINTER
                                      std::wistream*  p_input_stream, 
                                      const char*     CharacterEncodingName /* = 0x0   */,
                                      bool            ByteOrderReversionF   /* = false */)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_FIX(ANALYZER, __constructor_core)(this, p_input_stream, 
                                           CharacterEncodingName, ByteOrderReversionF, 
                                           0x0, 0);
}
#endif

#if defined(__QUEX_OPTION_UNIT_TEST) && ! defined (__QUEX_SETTING_PLAIN_C)
/* StrangeStreams are not for C-language stuff */
template<class UnderlyingStreamT> QUEX_INLINE
QUEX_TYPE_ANALYZER::QUEX_TYPE_ANALYZER(quex::StrangeStream<UnderlyingStreamT>*  p_input_stream, 
                                       const char*      CharacterEncodingName /* = 0x0   */,
                                       bool             ByteOrderReversionF   /* = false */)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_FIX(ANALYZER, __constructor_core)(this, p_input_stream, 
                                           CharacterEncodingName, ByteOrderReversionF, 
                                           0x0, 0);
}
#endif

QUEX_INLINE
QUEX_CONSTRUCTOR(ANALYZER, _FILE)(__QUEX_SETTING_THIS_POINTER
                                  std::FILE*   fh, 
                                  const char*  CharacterEncodingName /* = 0x0   */,
                                  bool         ByteOrderReversionF   /* = false */)
{
    if( fh == NULL ) QUEX_ERROR_EXIT("Error: received NULL as a file handle.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    QUEX_FIX(ANALYZER, __constructor_core)(this, fh, 
                                           CharacterEncodingName, ByteOrderReversionF, 
                                           0x0, 0);
}


QUEX_INLINE
QUEX_DESTRUCTOR(ANALYZER)(__QUEX_SETTING_THIS_POINTER) 
{
    QuexAnalyser_destruct(&this->base);
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE 
    QuexTokenQueue_destruct(&_token_queue);
#   endif
    if( __file_handle_allocated_by_constructor != 0x0 ) {
        std::fclose(__file_handle_allocated_by_constructor); 
    }
}

template<class InputHandleT> void
QUEX_FIX(ANALYZER, _reset)(QUEX_TYPE_ANALYZER*  me,
                           InputHandleT*        input_handle, 
                           const char*          CharacterEncodingName /* = 0x0 */) 
{
    me->base.__current_mode_p = 0x0; /* REQUIRED, for mode transition check */
    me->set_mode_brutally(__QUEX_SETTING_INITIAL_LEXER_MODE_ID);

    me->_mode_stack.end        = me->_mode_stack.begin;
    me->_mode_stack.memory_end = me->_mode_stack.begin + QUEX_SETTING_MODE_STACK_SIZE;

    QuexAnalyser_reset(&me->base, 
                       me->base.__current_mode_p->analyzer_function,
                       input_handle, 
                       CharacterEncodingName, 
                       QUEX_SETTING_TRANSLATION_BUFFER_SIZE);

#   ifdef __QUEX_OPTION_COUNTER
    QUEX_FIX(COUNTER, _init)(&me->counter);
#   endif

#   ifdef __QUEX_OPTION_TOKEN_POLICY_IS_QUEUE_BASED
    QuexTokenQueue_reset(me->_token_queue);
#   endif

#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    me->accumulator.clear();
#   endif

#   ifdef QUEX_OPTION_INCLUDE_STACK
    me->include_stack_delete();
#   endif

#   ifdef QUEX_OPTION_POST_CATEGORIZER
    me->post_categorizer.clear();
#   endif

    me->byte_order_reversion_set(false);
}

QUEX_NAMESPACE_COMPONENTS_CLOSE
