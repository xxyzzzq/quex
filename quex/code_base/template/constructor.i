// -*- C++ -*- vim:set syntax=cpp:
#include <quex/code_base/buffer/Buffer.i>
namespace quex { 


#if 0
inline QuexBufferFillerTypeEnum
CLASS::__constructor_filler_assert(QuexBufferFillerTypeEnum BFT, const char* CharacterEncodingName)
{
    QuexBufferFillerTypeEnum buffer_filler_type = BFT;
    if( CharacterEncodingName == 0x0 ) {
        if(    buffer_filler_type != QUEX_AUTO 
            && buffer_filler_type != QUEX_PLAIN 
            && buffer_filler_type != QUEX_PLAIN_INVERSE_BYTE_ORDER ) {
            QUEX_ERROR_EXIT("Input coding is left to '0x0' which means plain character encoding.\n"
                            "However, the buffer filler type is chosen to something different.\n");
        } else { 
            buffer_filler_type = BFT;
        }
    } else {
        if( buffer_filler_type == QUEX_PLAIN ) {
            QUEX_ERROR_EXIT("Input coding is specified but also the buffer filler type 'QUEX_PLAIN'.\n"
                            "The buffer filler type plain cannot handle character encodings.\n");
        } else if( buffer_filler_type == QUEX_PLAIN_INVERSE_BYTE_ORDER ) {
            QUEX_ERROR_EXIT("Input coding is specified but also the buffer filler type 'QUEX_PLAIN_INVERSE_BYTE_ORDER'.\n"
                            "The buffer filler type plain cannot handle character encodings.\n");
        } else if( buffer_filler_type == QUEX_AUTO ) {
#           if defined(QUEX_OPTION_ENABLE_ICONV) || defined(QUEX_OPTION_ENABLE_ICU)
            buffer_filler_type = QUEX_CONVERTER;
#           else
            QUEX_ERROR_EXIT("Use of buffer filler type QUEX_AUTO resulted in QUEX_CONVERTER\n" \
                            "Use of buffer filler type 'QUEX_CONVERTER' while option neither 'QUEX_OPTION_ENABLE_ICONV'\n" \
                            "nor 'QUEX_OPTION_ENABLE_ICU' is specified.\n");
#           endif
        }
    }
    return buffer_filler_type;
}
#endif


inline
CLASS::CLASS(QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
             size_t               BufferMemorySize,
             const char*          CharacterEncodingName /* = 0x0 */)
: 
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
{
    CLASS::__constructor_core<FILE>(0x0, CharacterEncodingName, 
                                    0x0, QUEX_SETTING_BUFFER_SIZE);
}

inline
CLASS::CLASS(const std::string&  Filename, 
             const char*         CharacterEncodingName /* = 0x0 */)
: 
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
{
    // Buffer: Size = (see macro def.), Fallback = 10 Characters
    // prefer FILE* based buffers, because we can turn low-level buffering off.
    // ownership of FILE* id passed to the input strategy of the buffer
    std::FILE* fh = std::fopen(Filename.c_str(), "rb");
    if( fh == NULL ) QUEX_ERROR_EXIT("Error on attempt to open specified file.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    __constructor_core(fh, CharacterEncodingName);
    // Recall, that this thing as to be deleted/closed
    __file_handle_allocated_by_constructor = fh;
}

inline
CLASS::CLASS(std::istream*   p_input_stream, 
             const char*     CharacterEncodingName /* = 0x0 */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, CharacterEncodingName);
}

inline
CLASS::CLASS(std::wistream*  p_input_stream, 
             const char*     CharacterEncodingName /* = 0x0 */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, CharacterEncodingName);
}

#if defined(__QUEX_OPTION_UNIT_TEST)
template<class UnderlyingStreamT> inline
CLASS::CLASS(quex::StrangeStream<UnderlyingStreamT>*  p_input_stream, 
             const char*                              CharacterEncodingName /* = 0x0 */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
{
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, CharacterEncodingName);
}
#endif

inline
CLASS::CLASS(std::FILE*   fh, 
             const char*  CharacterEncodingName /* = 0x0 */)
: 
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
{
    if( fh == NULL ) QUEX_ERROR_EXIT("Error: received NULL as a file handle.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    __constructor_core(fh, CharacterEncodingName);
}


inline
CLASS::~CLASS() 
{
    QuexAnalyser_destruct(this);
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE 
    delete [] _token_queue.begin;
#   endif
    if( __file_handle_allocated_by_constructor != 0x0 ) {
        std::fclose(__file_handle_allocated_by_constructor); 
    }
}

} // namespace quex
