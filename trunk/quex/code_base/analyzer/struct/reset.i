/* -*- C++ -*- vim:set syntax=cpp:
 * (C)  Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I

#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/analyzer/struct/reset>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

/* Level (0) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO(reset)  
{
    QUEX_NAME(BufferFiller)* filler = this->buffer.filler;

    if( filler ) {
        QUEX_NAME(BufferFiller_reset)(filler, filler->byte_loader);
    }

    QUEX_MEMBER_FUNCTION_CALL1(reset, BufferFiller, filler);
}

/* Level (1) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, file_name, 
                      const char* FileName, 
                      const char* CodecName /* = 0x0 */) 
{
    ByteLoader*   byte_loader;

    byte_loader = ByteLoader_FILE_new_from_file_name(FileName);
    if( ! byte_loader) return;

    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, byte_loader, CodecName); 
}

/* Level (2) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, FILE,
                      __QUEX_STD_FILE* fh, 
                      const char*      CodecName /* = 0x0   */)
{
    ByteLoader*   byte_loader;
    __quex_assert( fh );

    /* At the time of this writing 'stdin' as located in the C++ global namespace. 
     * This seemed suspicous to the author. To avoid compilation errors in the future
     * the test for the standard input is only active in 'C'. It is only about
     * user information anyway. So better no risks taken.      <fschaef 2010y02m06d> */
    setbuf(fh, 0);   /* turn off system based buffering! 
    **               ** this is essential to profit from the quex buffer! */
    byte_loader = ByteLoader_FILE_new(fh);
    if( ! byte_loader ) return;

    byte_loader->ownership = E_Ownership_LEXICAL_ANALYZER;
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, byte_loader, CodecName); 
}

#ifndef __QUEX_OPTION_PLAIN_C
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, istream,
                      std::istream*   istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    ByteLoader*   byte_loader;
    __quex_assert( istream_p );

    byte_loader = ByteLoader_stream_new(istream_p);
    if( ! byte_loader ) return;

    byte_loader->ownership = E_Ownership_LEXICAL_ANALYZER;
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, byte_loader, CodecName); 
}
#endif


#if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, wistream,
                      std::wistream*  istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    ByteLoader*   byte_loader;
    __quex_assert( istream_p );
    byte_loader = ByteLoader_stream_new(istream_p);
    if( ! byte_loader ) return;

    byte_loader->ownership = E_Ownership_LEXICAL_ANALYZER;
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, byte_loader, CodecName); 
}
#endif

#if defined(__QUEX_OPTION_UNIT_TEST) && ! defined (__QUEX_OPTION_PLAIN_C)
/* StrangeStreams are not for C-language stuff */
template<class UnderlyingStreamT> QUEX_INLINE
QUEX_MEMBER_FUNCTION2(reset, strange_stream, 
                      quex::StrangeStream<UnderlyingStreamT>*  istream_p, 
                      const char*                              CodecName /* = 0x0   */)
{
    ByteLoader*   byte_loader;
    __quex_assert( istream_p );
    byte_loader = ByteLoader_stream_new(istream_p);
    if( ! byte_loader ) return;

    byte_loader->ownership = E_Ownership_LEXICAL_ANALYZER;
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, byte_loader, CodecName); 
}
#endif


/* Level (3) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, ByteLoader,
                      ByteLoader*   byte_loader,
                      const char*   CodecName) 
{
    QUEX_NAME(BufferFiller)* filler = this->buffer.filler;
    QUEX_NAME(Asserts_construct)(CodecName);
    
    if( filler ) {
        QUEX_NAME(BufferFiller_reset)(filler, byte_loader);
    }
    else {
        filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, CodecName);
    }

    QUEX_MEMBER_FUNCTION_CALL1(reset, BufferFiller, filler);
}

/* Level (4) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION1(reset, BufferFiller,
                      QUEX_NAME(BufferFiller)* filler)
{
    if( filler != this->buffer.filler ) {
        this->buffer.filler->delete_self(this->buffer.filler);
        this->buffer.filler = filler;
    }
    else {
        /* Assume, that buffer filler has been reset.                        */
    }
    QUEX_NAME(Buffer_init_analyzis)(&this->buffer); 
    QUEX_MEMBER_FUNCTION_CALLO(basic_reset);
}

/* Level (5) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION3(reset, memory,
                      QUEX_TYPE_CHARACTER*    Memory,
                      const size_t            MemorySize,
                      QUEX_TYPE_CHARACTER*    EndOfFileP)
/* When memory is provided from extern, the 'external entity' is
 * responsible for filling it. There is no 'file/stream handle', no 'byte
 * loader', and 'no buffer filler'.                                          */
{
    QUEX_NAME(Buffer_destruct)(&this->buffer); 
    QUEX_NAME(Buffer_construct)(&this->buffer, 
                                (QUEX_NAME(BufferFiller)*)0,
                                Memory, MemorySize, EndOfFileP,
                                E_Ownership_EXTERNAL);
    QUEX_MEMBER_FUNCTION_CALLO(basic_reset);
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO(basic_reset)
{
    bool  byte_order_reversion_f = this->buffer.filler ? 
                                     this->buffer.filler->_byte_order_reversion_active_f
                                   : false;
    QUEX_NAME(Tokens_destruct)(this);
    QUEX_NAME(Tokens_construct)(this);

    QUEX_NAME(ModeStack_construct)(this);

    __QUEX_IF_INCLUDE_STACK(     this->_parent_memento = (QUEX_NAME(Memento)*)0);

    __QUEX_IF_STRING_ACCUMULATOR(QUEX_NAME(Accumulator_destruct)(&this->accumulator));
    __QUEX_IF_STRING_ACCUMULATOR(QUEX_NAME(Accumulator_construct)(&this->accumulator, this));

    __QUEX_IF_POST_CATEGORIZER(  QUEX_NAME(PostCategorizer_destruct)(&this->post_categorizer));
    __QUEX_IF_POST_CATEGORIZER(  QUEX_NAME(PostCategorizer_construct)(&this->post_categorizer));

    __QUEX_IF_COUNT(             QUEX_NAME(Counter_construct)(&this->counter); )

    QUEX_NAME(set_mode_brutally_by_id)(this, __QUEX_SETTING_INITIAL_LEXER_MODE_ID);

    if( this->buffer.filler && byte_order_reversion_f )
    {
        this->buffer.filler->_byte_order_reversion_active_f = true;
    }
    QUEX_MEMBER_FUNCTION_CALLO(user_reset);
}


QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I */
