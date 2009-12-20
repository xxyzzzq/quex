/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                   */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__CONSTRUCTOR
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__CONSTRUCTOR

#include <quex/code_base/buffer/Buffer.i>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_FUNC(construct_memory)(QUEX_TYPE_ANALYZER*  me,
                            QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                            size_t               BufferMemorySize,
                            const char*          CharacterEncodingName /* = 0x0   */,
                            bool                 ByteOrderReversionF   /* = false */)
{
    size_t  memory_size = BufferMemoryBegin != 0 ? BufferMemorySize 
                          :                        QUEX_SETTING_BUFFER_SIZE;

    __quex_assert(memory_size > 2);

    QUEX_FUNC(constructor_core)(me, (void*)0x0, 
                                CharacterEncodingName, ByteOrderReversionF, 
                                BufferMemoryBegin, memory_size);
}

QUEX_INLINE void
QUEX_FUNC(construct_file_name)(QUEX_TYPE_ANALYZER* me,
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
    QUEX_FUNC(constructor_core)(me, fh, 
                                CharacterEncodingName, ByteOrderReversionF, 
                                0x0, 0);
    // Recall, that this thing as to be deleted/closed
    me->__file_handle_allocated_by_constructor = fh;
}

QUEX_INLINE void
QUEX_FUNC(construct_FILE)(QUEX_TYPE_ANALYZER* me,
                          std::FILE*          fh, 
                          const char*         CharacterEncodingName /* = 0x0   */,
                          bool                ByteOrderReversionF   /* = false */)
{
    if( fh == NULL ) QUEX_ERROR_EXIT("Error: received NULL as a file handle.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    QUEX_FUNC(constructor_core)(me, fh, 
                                CharacterEncodingName, ByteOrderReversionF, 
                                0x0, 0);
}

QUEX_INLINE void
QUEX_FUNC(construct_istream)(QUEX_TYPE_ANALYZER* me,
                             std::istream*       p_input_stream, 
                             const char*         CharacterEncodingName /* = 0x0   */,
                             bool                ByteOrderReversionF   /* = false */)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_FUNC(constructor_core)(me, p_input_stream, 
                                CharacterEncodingName, ByteOrderReversionF, 
                                0x0, 0);
}


#if defined(__QUEX_OPTION_WCHAR_T)
QUEX_INLINE void
QUEX_FUNC(construct_wistream)(QUEX_TYPE_ANALYZER* me,
                              std::wistream*      p_input_stream, 
                              const char*         CharacterEncodingName /* = 0x0   */,
                              bool                ByteOrderReversionF   /* = false */)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_FUNC(constructor_core)(me, p_input_stream, 
                                CharacterEncodingName, ByteOrderReversionF, 
                                0x0, 0);
}
#endif

QUEX_INLINE void
QUEX_FUNC(destruct)(QUEX_TYPE_ANALYZER* me) 
{
    QUEX_NAME(AnalyzerData_destruct)(me);
}

TEMPLATE_IN(InputHandleT) void
QUEX_FUNC(reset)(QUEX_TYPE_ANALYZER*  me,
                 InputHandleT*        input_handle, 
                 const char*          CharacterEncodingName /* = 0x0 */) 
{
    QUEX_NAME(AnalyzerData_reset)((QUEX_NAME(AnalyzerData)*)me, input_handle, 
                                  CharacterEncodingName, 
                                  QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
    me->__current_mode_p = 0x0; /* REQUIRED, for mode transition check */
    QUEX_FUNC(set_mode_brutally_by_id)(me, __QUEX_SETTING_INITIAL_LEXER_MODE_ID);
}

QUEX_INLINE void 
QUEX_FUNC(reset_plain)(QUEX_TYPE_ANALYZER*  me,
                       const char*          CharacterEncodingName /* = 0x0 */)
{ QUEX_FUNC(reset)(me, (FILE*)0x0, CharacterEncodingName); }

#if ! defined(__QUEX_SETTING_PLAIN_C)
QUEX_INLINE
QUEX_MEMBER(QUEX_TYPE_ANALYZER)(QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                                size_t               BufferMemorySize,
                                const char*          CharacterEncodingName /* = 0x0   */,
                                bool                 ByteOrderReversionF   /* = false */)
{ QUEX_FUNC(construct_memory)(this, BufferMemoryBegin, BufferMemorySize, CharacterEncodingName, ByteOrderReversionF); }

QUEX_INLINE
QUEX_MEMBER(QUEX_TYPE_ANALYZER)(const std::string&  Filename, 
                                const char*         CharacterEncodingName /* = 0x0   */,
                                bool                ByteOrderReversionF   /* = false */)
{ QUEX_FUNC(construct_file_name)(this, Filename, CharacterEncodingName, ByteOrderReversionF); }

QUEX_INLINE
QUEX_MEMBER(QUEX_TYPE_ANALYZER)(std::FILE*   fh, 
                                const char*  CharacterEncodingName /* = 0x0   */,
                                bool         ByteOrderReversionF   /* = false */)
{ QUEX_FUNC(construct_FILE)(this, fh, CharacterEncodingName, ByteOrderReversionF); }

QUEX_INLINE
QUEX_MEMBER(QUEX_TYPE_ANALYZER)(std::istream*   p_input_stream, 
                                const char*     CharacterEncodingName /* = 0x0   */,
                                bool            ByteOrderReversionF   /* = false */)
{ QUEX_FUNC(construct_istream)(this, p_input_stream, CharacterEncodingName, ByteOrderReversionF); }

#if defined(__QUEX_OPTION_WCHAR_T)
QUEX_INLINE
QUEX_MEMBER(QUEX_TYPE_ANALYZER)(std::wistream*  p_input_stream, 
                                const char*     CharacterEncodingName /* = 0x0   */,
                                bool            ByteOrderReversionF   /* = false */)
{ QUEX_FUNC(construct_wistream)(this, p_input_stream, CharacterEncodingName, ByteOrderReversionF); }
#endif

#if defined(__QUEX_OPTION_UNIT_TEST) && ! defined (__QUEX_SETTING_PLAIN_C)
/* StrangeStreams are not for C-language stuff */
template<class UnderlyingStreamT> QUEX_INLINE
QUEX_MEMBER(QUEX_TYPE_ANALYZER)(quex::StrangeStream<UnderlyingStreamT>*  p_input_stream, 
                                const char*      CharacterEncodingName /* = 0x0   */,
                                bool             ByteOrderReversionF   /* = false */)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_FUNC(constructor_core)(this, p_input_stream, 
                                CharacterEncodingName, ByteOrderReversionF, 
                                0x0, 0);
}
#endif

QUEX_INLINE
QUEX_MEMBER(~QUEX_TYPE_ANALYZER)() 
{ QUEX_FUNC(destruct)(this); }

template<class InputHandleT> void
QUEX_MEMBER(reset)(InputHandleT* input_handle, const char* CharacterEncodingName /* = 0x0 */) 
{ QUEX_FUNC(reset)(this, input_handle, CharacterEncodingName); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__CONSTRUCTOR */
