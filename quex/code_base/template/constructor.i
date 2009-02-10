// -*- C++ -*- vim:set syntax=cpp:
#include <quex/code_base/buffer/Buffer.i>
namespace quex { 


inline QuexBufferFillerTypeEnum
CLASS::__constructor_filler_assert(QuexBufferFillerTypeEnum BFT, const char* IANA_InputCodingName)
{
    QuexBufferFillerTypeEnum buffer_filler_type = BFT;
    if( IANA_InputCodingName == 0x0 ) {
        if( buffer_filler_type != QUEX_AUTO && buffer_filler_type != QUEX_PLAIN ) {
            QUEX_ERROR_EXIT("Input coding is left to '0x0' which means plain character encoding.\n"
                            "However, the buffer filler type is chosen to something different.\n");
        } else { 
            buffer_filler_type = BFT;
        }
    } else {
        if( buffer_filler_type == QUEX_PLAIN ) {
            QUEX_ERROR_EXIT("Input coding is specified but also the buffer filler type 'plain'.\n"
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


inline
CLASS::CLASS()
: 
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
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
    CLASS::__constructor_core<FILE>(0x0, QUEX_MEMORY, 0x0);
}

inline
CLASS::CLASS(const std::string&       Filename, 
             const char*              IANA_InputCodingName /* = 0x0 */, 
             QuexBufferFillerTypeEnum BFT /* = QUEX_AUTO */)
: 
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
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
    QuexBufferFillerTypeEnum bft = __constructor_filler_assert(BFT, IANA_InputCodingName);
    // Buffer: Size = (see macro def.), Fallback = 10 Characters
    // prefer FILE* based buffers, because we can turn low-level buffering off.
    // ownership of FILE* id passed to the input strategy of the buffer
    std::FILE* fh = std::fopen(Filename.c_str(), "rb");
    if( fh == NULL ) QUEX_ERROR_EXIT("Error on attempt to open specified file.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    __constructor_core(fh, bft, IANA_InputCodingName);
    // Recall, that this thing as to be deleted/closed
    __file_handle_allocated_by_constructor = fh;
}

inline
CLASS::CLASS(std::istream*            p_input_stream, 
             const char*              IANA_InputCodingName /* = 0x0 */,
             QuexBufferFillerTypeEnum BFT /* = QUEX_AUTO */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
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
    QuexBufferFillerTypeEnum bft = __constructor_filler_assert(BFT, IANA_InputCodingName);
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, bft, IANA_InputCodingName);
}

inline
CLASS::CLASS(std::wistream*           p_input_stream, 
             const char*              IANA_InputCodingName /* = 0x0 */,
             QuexBufferFillerTypeEnum BFT /* = QUEX_AUTO */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
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
    QuexBufferFillerTypeEnum bft = __constructor_filler_assert(BFT, IANA_InputCodingName);
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, bft, IANA_InputCodingName);
}

#if defined(__QUEX_OPTION_UNIT_TEST)
template<class UnderlyingStreamT> inline
CLASS::CLASS(quex::StrangeStream<UnderlyingStreamT>*  p_input_stream, 
             const char*                              IANA_InputCodingName /* = 0x0 */,
             QuexBufferFillerTypeEnum                 BFT /* = QUEX_AUTO */)
:
    // NOTE: dynamic_cast<>() would request derived class to be **defined**! 
    // Decision: "ease-of-use preceeds protection against a tremendous stupidity."
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
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
    QuexBufferFillerTypeEnum bft = __constructor_filler_assert(BFT, IANA_InputCodingName);
    if( p_input_stream == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    __constructor_core(p_input_stream, bft, IANA_InputCodingName);
}
#endif

inline
CLASS::CLASS(std::FILE* fh, 
             const char*              IANA_InputCodingName /* = 0x0 */,
             QuexBufferFillerTypeEnum BFT /* = QUEX_AUTO */)
: 
    self(*((__QUEX_SETTING_DERIVED_CLASS_NAME*)this)),
    __file_handle_allocated_by_constructor(0x0)
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
    QuexBufferFillerTypeEnum bft = __constructor_filler_assert(BFT, IANA_InputCodingName);
    if( fh == NULL ) QUEX_ERROR_EXIT("Error: received NULL as a file handle.");
    setbuf(fh, 0);   // turn off system based buffering!
    //               // this is essential to profit from the quex buffer!
    __constructor_core(fh, bft, IANA_InputCodingName);
}


inline
CLASS::~CLASS() 
{
    QuexAnalyser_destruct(this);
#   ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE 
    delete _token_queue;
#   endif
    if( __file_handle_allocated_by_constructor != 0x0 ) {
        std::fclose(__file_handle_allocated_by_constructor); 
    }
}

} // namespace quex
