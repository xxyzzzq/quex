/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2004-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_NAME(Accumulator) must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I

#ifndef   QUEX_TYPE_ANALYZER
#   error "Macro QUEX_TYPE_ANALYZER must be defined before inclusion of this file."
#endif


#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

/* Level (1) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(include_push, file_name, 
                      const char* FileName, 
                      const char* CodecName /* = 0x0 */) 
{
    /* Prefer FILE* based byte-loaders, because turn low-level buffering can be
     * turned off.                                                               */
    __QUEX_STD_FILE*   fh = __QUEX_STD_fopen(FileName, "rb");

    /* ByteLoader will overtake ownership over 'fh', so we do not need to 
     * take care over 'free' and 'fclose'.                                       */
    QUEX_MEMBER_FUNCTION_CALL2(include_push, FILE, fh, CodecName);
}

/* Level (2) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(include_push, FILE,
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
    QUEX_MEMBER_FUNCTION_CALL2(include_push, ByteLoader, 
                               ByteLoader_FILE_new(fh), CodecName); 
}

#ifndef __QUEX_OPTION_PLAIN_C
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(include_push, istream,
                      std::istream*   istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    __quex_assert( istream_p );

    QUEX_MEMBER_FUNCTION_CALL2(include_push, ByteLoader, 
                               ByteLoader_stream_new(istream_p), CodecName); 
}
#endif


#if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(include_push, wistream,
                      std::wistream*  istream_p, 
                      const char*     CodecName /* = 0x0   */)
{
    __quex_assert( istream_p );
    QUEX_MEMBER_FUNCTION_CALL2(include_push, ByteLoader, 
                               ByteLoader_stream_new(istream_p), CodecName); 
}
#endif

#if defined(__QUEX_OPTION_UNIT_TEST) && ! defined (__QUEX_OPTION_PLAIN_C)
/* StrangeStreams are not for C-language stuff */
template<class UnderlyingStreamT> QUEX_INLINE
QUEX_MEMBER_FUNCTION2(include_push, strange_stream, 
                      quex::StrangeStream<UnderlyingStreamT>*  istream_p, 
                      const char*                              CodecName /* = 0x0   */)
{
    if( istream_p == NULL ) QUEX_ERROR_EXIT("Error: received NULL as pointer to input stream.");
    QUEX_MEMBER_FUNCTION_CALL2(include_push, ByteLoader,
                               ByteLoader_stream_new(istream_p), CodecName); 
}
#endif


/* Level (3) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION2(include_push, ByteLoader,
                      ByteLoader*   byte_loader,
                      const char*   CodecName) 
{
    QUEX_NAME(BufferFiller)* filler;
    QUEX_NAME(Asserts_construct)(CodecName);

    filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, CodecName);
    
    QUEX_MEMBER_FUNCTION_CALL1(include_push, BufferFiller, filler);
}

/* Level (4) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION1(include_push, BufferFiller,
                      QUEX_NAME(BufferFiller)* filler)
{
    QUEX_NAME(Buffer_destruct)(&this->buffer); 
    QUEX_NAME(Buffer_construct)(&this->buffer, filler, QUEX_SETTING_BUFFER_SIZE); 
    QUEX_MEMBER_FUNCTION_CALLO(basic_include_push);
}

/* Level (5) __________________________________________________________________
 *                                                                           */
QUEX_INLINE void
QUEX_MEMBER_FUNCTION3(include_push, memory,
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
    QUEX_MEMBER_FUNCTION_CALLO(basic_include_push);
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO(basic_include_push)
{
    bool                byte_order_reversion_f = this->buffer.filler ? 
                                                   this->buffer.filler->_byte_order_reversion_active_f
                                                 : false;
    QUEX_NAME(Memento)* memento = (QUEX_NAME(Memento)*)QUEXED(MemoryManager_allocate)(
                                     sizeof(QUEX_NAME(Memento)), QUEXED(MemoryObjectType_MEMENTO));
#   ifndef __QUEX_OPTION_PLAIN_C
    /* Use placement 'new' for explicit call of constructor. 
     * Necessary in C++: Trigger call to constructor for user defined members.   */
    new ((void*)memento) QUEX_NAME(Memento);
#   endif

    memento->_parent_memento                  = this->_parent_memento;
    memento->buffer                           = this->buffer;
    memento->__current_mode_p                 = this->__current_mode_p; 
    memento->current_analyzer_function        = this->current_analyzer_function;
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    memento->DEBUG_analyzer_function_at_entry = this->DEBUG_analyzer_function_at_entry;
#   endif
    __QUEX_IF_COUNT( memento->counter         = this->counter);
    this->_parent_memento = memento;

    __QUEX_IF_COUNT( QUEX_NAME(Counter_construct)(&this->counter); )

    if( this->buffer.filler && byte_order_reversion_f )
    {
        this->buffer.filler->_byte_order_reversion_active_f = true;
    }

    /* Deriberately not subject to include handling:
     *    -- Mode stack.
     *    -- Token and token queues.
     *    -- Post categorizer.                                                 */
    QUEX_MEMBER_FUNCTION_CALLO1(user_memento_pack, memento);
}   

QUEX_INLINE bool
QUEX_MEMBER_FUNCTIONO(include_pop) 
{
    QUEX_NAME(Memento)* memento;
    /* Not included? return 'false' to indicate we're on the top level   */
    if( ! this->_parent_memento ) return false; 

    QUEX_NAME(Buffer_destruct)(&this->buffer);
    /* memento_unpack():
     *    => Current mode
     *           => __current_mode_p 
     *              current_analyzer_function                                       
     *              DEBUG_analyzer_function_at_entry                                   
     *    => Line/Column Counters
     *
     * Unchanged by memento_unpack():
     *    -- Mode stack
     *    -- Tokens and token queues.
     *    -- Accumulator.
     *    -- Post categorizer.
     *    -- File handle by constructor                                  */
          
    /* Copy Back of content that was stored upon inclusion.              */
    memento = this->_parent_memento;

    this->_parent_memento                  = memento->_parent_memento;
    this->buffer                           = memento->buffer;
    this->__current_mode_p                 = memento->__current_mode_p; 
    this->current_analyzer_function        = memento->current_analyzer_function;
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    this->DEBUG_analyzer_function_at_entry = memento->DEBUG_analyzer_function_at_entry;
#   endif
    __QUEX_IF_COUNT(this->counter          = memento->counter);

    QUEX_MEMBER_FUNCTION_CALLO1(user_memento_unpack,memento);

#   ifndef __QUEX_OPTION_PLAIN_C
    /* Counterpart to placement new: Explicit destructor call.
     * Necessary in C++: Trigger call to destructor for user defined members.  */
    memento->~QUEX_NAME(Memento_tag)();
#   endif

    QUEXED(MemoryManager_free)((void*)memento, QUEXED(MemoryObjectType_MEMENTO)); 

    /* Return to including file succesful */
    return true;
}
     
QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO(include_stack_delete)
{
    while( this->_parent_memento ) {
        if( ! QUEX_MEMBER_FUNCTION_CALLO(include_pop) ) {
            QUEX_ERROR_EXIT("Error during deletion of include stack.");
        }
    }
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I */
