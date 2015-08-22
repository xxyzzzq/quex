/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                   */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I

#include <quex/code_base/buffer/Buffer.i>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN


/* Level (1) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, file_name, 
                      const char* FileName, 
                      const char* CodecName /* = 0x0 */) 
{
    /* Prefer FILE* based byte-loaders, because turn low-level buffering can be
     * turned off.                                                               */
    __QUEX_STD_FILE*   fh = __QUEX_STD_fopen(FileName, "rb");

    /* ByteLoader will overtake ownership over 'fh', so we do not need to 
     * take care over 'free' and 'fclose'.                                       */
    QUEX_MEMBER_FUNCTION_CALL2(reset, FILE, fh, CodecName);
}

/* Level (2) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, FILE,
                      __QUEX_STD_FILE*    fh, 
                      const char*         CodecName /* = 0x0   */)
{
    __quex_assert( ! fh );

    /* At the time of this writing 'stdin' as located in the C++ global namespace. 
     * This seemed suspicous to the author. To avoid compilation errors in the future
     * the test for the standard input is only active in 'C'. It is only about
     * user information anyway. So better no risks taken.      <fschaef 2010y02m06d> */
    setbuf(fh, 0);   /* turn off system based buffering! 
    **               ** this is essential to profit from the quex buffer! */
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, 
                               ByteLoader_FILE_new(fh), CodecName); 
}

#ifndef __QUEX_OPTION_PLAIN_C
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, istream,
                      std::istream*   istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    __quex_assert( ! istream_p );

    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, 
                               ByteLoader_stream_new(istream_p), CodecName); 
}
#endif


#if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, wistream,
                      std::wistream*  istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    __quex_assert( ! istream_p );
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader, 
                               ByteLoader_stream_new(istream_p), CodecName); 
}
#endif

#if defined(__QUEX_OPTION_UNIT_TEST) && ! defined (__QUEX_OPTION_PLAIN_C)
/* StrangeStreams are not for C-language stuff */
template<class UnderlyingStreamT> QUEX_INLINE
QUEX_MEMBER_FUNCTION2(reset, strange_stream, 
                      quex::StrangeStream<UnderlyingStreamT>*  istream_p, 
                      const char*                              CodecName /* = 0x0   */)
{
    if( istream_p == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_MEMBER_FUNCTION_CALL2(reset, ByteLoader,
                               ByteLoader_stream_new(istream_p), CodecName); 
}
#endif


/* Level (3) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(reset, ByteLoader,
                      ByteLoader*   byte_loader,
                      const char*   CodecName) 
{
    QUEX_NAME(BufferFiller)* filler;
    QUEX_NAME(Asserts_construct)(CodecName);

    if( this->buffer.filler )
    {
        QUEX_NAME(BufferFiller_delete_self)(this->buffer.filler);
    }
    filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, CodecName);
    
    QUEX_MEMBER_FUNCTION_CALL1(reset, BufferFiller, filler);
}

/* Level (4) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION1(reset, BufferFiller,
                      QUEX_NAME(BufferFiller)* filler)
{
    QUEX_NAME(Buffer_destruct)(&this->buffer); 
    QUEX_NAME(Buffer_construct)(&this->buffer, filler, QUEX_SETTING_BUFFER_SIZE); 
    QUEX_MEMBER_FUNCTION_CALL(basic_reset,);
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
    QUEX_NAME(Buffer_construct_with_memory)(&this->buffer, 
                                            (QUEX_NAME(BufferFiller)*)0,
                                            Memory, MemorySize, EndOfFileP,
                                            /* External */ true);
    QUEX_MEMBER_FUNCTION_CALL(basic_reset,);
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTION(basic_reset,)
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
    QUEX_MEMBER_FUNCTION_CALL(user_reset, );
}


QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I */
