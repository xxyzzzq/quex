// -*- C++ -*- vim:set syntax=cpp:
inline
CLASS::CLASS(const std::string& Filename, const char* IConvInputCodingName /* = 0x0 */)
: 
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this))
#   ifdef QUEX_OPTION_INCLUDE_STACK_SUPPORT
    , include_stack(this)
#   endif
#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    , accumulator(this)
#   endif
#   ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT
    , counter(this)
#   endif
{
    // Buffer: Size = (see macro def.), Fallback = 10 Characters
    // prefer FILE* based buffers, because we can turn low-level buffering off.
    // ownership of FILE* id passed to the input strategy of the buffer
    std::FILE* fh = std::fopen(Filename.c_str(), "r");
    if( fh == NULL ) throw std::runtime_error("Error on attempt to open specified file.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    __constructor_core(fh, IConvInputCodingName);
}

inline
CLASS::CLASS(std::istream* p_input_stream, const char* IConvInputCodingName /* = 0x0 */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this))
#   ifdef QUEX_OPTION_INCLUDE_STACK_SUPPORT
    , include_stack(this)
#   endif
#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    , accumulator(this)
#   endif
#   ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT
    , counter(this)
#   endif
{
    if( p_input_stream == NULL ) throw std::runtime_error("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, IConvInputCodingName);
}

inline
CLASS::CLASS(std::FILE* fh, const char* IConvInputCodingName /* = 0x0 */)
: 
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this))
#   ifdef QUEX_OPTION_INCLUDE_STACK_SUPPORT
    , include_stack(this)
#   endif
#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    , accumulator(this)
#   endif
#   ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT
    , counter(this)
#   endif
{
    if( fh == NULL ) throw std::runtime_error("Error: received NULL as a file handle.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    __constructor_core(fh, IConvInputCodingName);
}

template <class InputHandle> inline
quex::buffer<QUEX_CHARACTER_TYPE>*
CLASS::create_buffer(InputHandle* input_handle, const char* IConvInputCodingName /* = 0x0 */)
{
    fixed_size_character_stream<QUEX_CHARACTER_TYPE>*  is = 0x0;

    if( IConvInputCodingName != 0x0 ) {
#       ifdef  __QUEX_CORE_OPTION_ICONV_BUFFERS_ENABLED
        is = new fixed_size_character_stream_iconv<InputHandle, QUEX_CHARACTER_TYPE>
                       (input_handle, 
                        iconv_translation_buffer, QUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE,
                        IConvInputCodingName,     QUEX_SETTING_CORE_ENGINE_CHARACTER_CODING); 

#       else
        return 0x0;
#       endif
    }
    else {
        is = new fixed_size_character_stream_plain<InputHandle, QUEX_CHARACTER_TYPE>(input_handle);
    }
    return new buffer<QUEX_CHARACTER_TYPE>(is, QUEX_SETTING_BUFFER_SIZE, 
                                           QUEX_SETTING_BUFFER_FALLBACK_SIZE,
                                           (QUEX_CHARACTER_TYPE)QUEX_SETTING_BUFFER_LIMIT_CODE);
}

inline
CLASS::~CLASS() 
{
    QUEX_CORE_ANALYSER_STRUCT::__buffer->close_input();
    delete QUEX_CORE_ANALYSER_STRUCT::__buffer;
#   ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE 
    delete _token_queue;
#   endif
}

