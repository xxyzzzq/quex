/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2015 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__CONSTRUCTOR_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__CONSTRUCTOR_I

#include <quex/code_base/buffer/Buffer.i>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN
                    
QUEX_INLINE void   QUEX_NAME(Asserts_user_memory)(QUEX_TYPE_ANALYZER*  me,
                             QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                             size_t               BufferMemorySize,
                             QUEX_TYPE_CHARACTER* EndOfContentP  /* = 0x0   */);
QUEX_INLINE void   QUEX_NAME(Asserts_construct)(const char* CodecName);
QUEX_INLINE void   QUEX_NAME(Tokens_construct)(QUEX_TYPE_ANALYZER* me);
QUEX_INLINE void   QUEX_NAME(Tokens_reset)(QUEX_TYPE_ANALYZER* me);
QUEX_INLINE void   QUEX_NAME(Tokens_destruct)(QUEX_TYPE_ANALYZER* me);
QUEX_INLINE void   QUEX_NAME(ModeStack_construct)(QUEX_TYPE_ANALYZER* me);
QUEX_INLINE void   QUEX_NAME(BufferFiller_DEFAULT)(QUEX_TYPE_ANALYZER* me);


/* Level (1) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(construct, file_name,
                      const char*  Filename, 
                      const char*  CodecName)
{
    /* Prefer FILE* based byte-loaders, because turn low-level buffering can   
     * be turned off.                                                        */
    __QUEX_STD_FILE*   fh = __QUEX_STD_fopen(Filename, "rb");

    /* ByteLoader will overtake ownership over 'fh', so we do not need to 
     * take care over 'free' and 'fclose'.                                   */
    QUEX_MEMBER_FUNCTION_CALL2(construct, FILE, fh, CodecName);
}

/* Level (2) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(construct, FILE,
                      __QUEX_STD_FILE*    fh, 
                      const char*         CodecName /* = 0x0   */)
{
    __quex_assert( fh );

    /* At the time of this writing 'stdin' as located in the C++ global namespace. 
     * This seemed suspicous to the author. To avoid compilation errors in the future
     * the test for the standard input is only active in 'C'. It is only about
     * user information anyway. So better no risks taken.      <fschaef 2010y02m06d> */
    setbuf(fh, 0);   /* turn off system based buffering! 
    **               ** this is essential to profit from the quex buffer! */
    QUEX_MEMBER_FUNCTION_CALL2(construct, ByteLoader, ByteLoader_FILE_new(fh), 
                           CodecName); 
}

#ifndef __QUEX_OPTION_PLAIN_C
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(construct, istream,
                      std::istream*   istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    __quex_assert( istream_p );
    QUEX_MEMBER_FUNCTION_CALL2(construct, ByteLoader, ByteLoader_stream_new(istream_p), 
                           CodecName); 
}
#endif


#if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void 
QUEX_MEMBER_FUNCTION2(construct, wistream,
                      std::wistream*  istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    __quex_assert( istream_p );
    QUEX_MEMBER_FUNCTION_CALL2(construct, ByteLoader, ByteLoader_stream_new(istream_p), 
                           CodecName); 
}
#endif

#if defined(__QUEX_OPTION_UNIT_TEST) && ! defined (__QUEX_OPTION_PLAIN_C)
/* StrangeStreams are not for C-language stuff */
template<class UnderlyingStreamT> QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(construct, strange_stream, 
                      quex::StrangeStream<UnderlyingStreamT>*  istream_p, 
                      const char*                              CodecName /* = 0x0   */)
{
    if( istream_p == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_MEMBER_FUNCTION_CALL2(construct, ByteLoader, ByteLoader_stream_new(istream_p), 
                           CodecName); 
}
#endif


/* Level (3) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(construct, ByteLoader,
                      ByteLoader*   byte_loader,
                      const char*   CodecName) 
{
    QUEX_NAME(BufferFiller)* filler;
    QUEX_NAME(Asserts_construct)(CodecName);

    filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, CodecName);
    
    QUEX_MEMBER_FUNCTION_CALL1(construct, BufferFiller, filler);
}

/* Level (4) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION1(construct, BufferFiller,
                      QUEX_NAME(BufferFiller)* filler)
{
    QUEX_NAME(Buffer_construct)(&this->buffer, filler, QUEX_SETTING_BUFFER_SIZE); 
    QUEX_MEMBER_FUNCTION_CALL(basic_constructor,);
}

/* Level (5) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION3(construct, memory,
                      QUEX_TYPE_CHARACTER*    Memory,
                      const size_t            MemorySize,
                      QUEX_TYPE_CHARACTER*    EndOfFileP)
/* When memory is provided from extern, the 'external entity' is
 * responsible for filling it. There is no 'file/stream handle', no 'byte
 * loader', and 'no buffer filler'.                                          */
{
    QUEX_NAME(Buffer_construct_with_memory)(&this->buffer, 
                                            QUEX_NAME(BufferFiller*)0,
                                            Memory, MemorySize, EndOfFileP,
                                            /* External */ true);
    QUEX_MEMBER_FUNCTION_CALL(basic_constructor,);
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTION(basic_constructor,)
{
    QUEX_NAME(Tokens_construct)(this);
    QUEX_NAME(ModeStack_construct)(this);
    __QUEX_IF_INCLUDE_STACK(     this->_parent_memento = (QUEX_NAME(Memento)*)0);
    __QUEX_IF_STRING_ACCUMULATOR(QUEX_NAME(Accumulator_construct)(&this->accumulator, this));
    __QUEX_IF_POST_CATEGORIZER(  QUEX_NAME(PostCategorizer_construct)(&this->post_categorizer));
    __QUEX_IF_COUNT(             QUEX_NAME(Counter_construct)(&this->counter); )

    QUEX_NAME(set_mode_brutally)(this, this->mode_db[__QUEX_SETTING_INITIAL_LEXER_MODE_ID]);

    QUEX_MEMBER_FUNCTION(user_constructor,)();
}

QUEX_INLINE void
QUEX_DESTRUCTOR() 
{
    QUEX_NAME(Tokens_destruct)(this);
    __QUEX_IF_INCLUDE_STACK(QUEX_NAME(include_stack_delete)((QUEX_TYPE_ANALYZER*)this));
    /* IMPORTANT: THE ACCUMULATOR CAN ONLY BE DESTRUCTED AFTER THE INCLUDE 
     *            STACK HAS BEEN DELETED. OTHERWISE, THERE MIGHT BE LEAKS. 
     * TODO: Why? I cannot see a reason <fschaef 15y08m03d>                  */
    __QUEX_IF_STRING_ACCUMULATOR( QUEX_NAME(Accumulator_destruct)(&this->accumulator));
    __QUEX_IF_POST_CATEGORIZER(   QUEX_NAME(PostCategorizer_destruct)(&this->post_categorizer));

    QUEX_NAME(Buffer_destruct)(&this->buffer);
}

QUEX_INLINE void
QUEX_NAME(Asserts_user_memory)(QUEX_TYPE_ANALYZER*  me,
                               QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                               size_t               BufferMemorySize,
                               QUEX_TYPE_CHARACTER* EndOfContentP  /* = 0x0   */)
{
    size_t  memory_size = BufferMemoryBegin ? BufferMemorySize 
                          :                   QUEX_SETTING_BUFFER_SIZE;
#   ifdef QUEX_OPTION_ASSERTS
    QUEX_TYPE_CHARACTER*   iterator = 0x0;

    __quex_assert(memory_size == 0 || memory_size > 2);
    if( BufferMemoryBegin ) {
        /* End of File must be inside the buffer, because we assume that the buffer
         * contains all that is required.                                           */
        if( BufferMemorySize <= QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2) {
            QUEX_ERROR_EXIT("\nConstructor: Provided memory size must be more than 2 greater than\n"
                            "Constructor: QUEX_SETTING_BUFFER_MIN_FALLBACK_N. If in doubt, specify\n"
                            "Constructor: -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 as compile option.\n");
        }
        if(    BufferEndOfContentP < BufferMemoryBegin 
            || BufferEndOfContentP > (BufferMemoryBegin + BufferMemorySize - 1)) {
            QUEX_ERROR_EXIT("\nConstructor: Argument 'BufferEndOfContentP' must be inside the provided memory\n"
                            "Constructor: buffer (speficied by 'BufferMemoryBegin' and 'BufferMemorySize').\n"
                            "Constructor: Note, that the last element of the buffer is to be filled with\n"
                            "Constructor: the buffer limit code character.\n");
        }
    }
    if( BufferEndOfContentP ) {
        __quex_assert(BufferEndOfContentP >  BufferMemoryBegin);
        __quex_assert(BufferEndOfContentP <= BufferMemoryBegin + memory_size - 1);

        /* The memory provided must be initialized. If it is not, then that's wrong.
         * Try to detect me by searching for BLC and PTC.                         */
        for(iterator = BufferMemoryBegin + 1; iterator != BufferEndOfContentP; ++iterator) {
            if(    *iterator == QUEX_SETTING_BUFFER_LIMIT_CODE 
                || *iterator == QUEX_SETTING_PATH_TERMINATION_CODE ) {
                QUEX_ERROR_EXIT("\nConstructor: Buffer limit code and/or path termination code appeared in buffer\n"
                                "Constructor: when pointed to user memory. Note, that the memory pointed to must\n"
                                "Constructor: be initialized! You might redefine QUEX_SETTING_PATH_TERMINATION_CODE\n"
                                "Constructor: and/or QUEX_SETTING_PATH_TERMINATION_CODE; or use command line arguments\n"
                                "Constructor: '--buffer-limit' and '--path-termination'.");
            }
        }
    }
#   endif
}


QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__CONSTRUCTOR_I */
