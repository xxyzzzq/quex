// : -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2007 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_

#include <cstring>
#include <quex/code_base/buffer/FixedSizeCharacterStream>

namespace quex {
#   define TEMPLATE_IN  template<class CharacterCarrierType> inline
#   define CLASS        Buffer<CharacterCarrierType>   
#   define BASE         QuexBufferCore<CharacterCarrierType>   

#   ifdef QUEX_OPTION_ACTIVATE_ASSERTS
#       define  QUEX_BUFFER_ASSERT_CONSISTENCY()                                             \
        {                                                                                    \
            /* NOTE: No assumptions can be made in general on the relation between    */     \
            /*       _input_p and _lexeme_start_p, since for forwards lexing        */     \
            /*       _input_p comes before _lexeme_start_p, wherelse for back-      */     \
            /*       ward lexing this is vice versa.                                  */     \
            /*       See "code_base/core_engine/definitions-quex-buffer.h"            */     \
            __quex_assert(BASE::_memory.front()    <  BASE::_memory.back());                             \
            __quex_assert(BASE::_input_p         >= BASE::_memory.front());                            \
            __quex_assert(_lexeme_start_p    >= BASE::_memory.front());                            \
            __quex_assert(*(BASE::_memory.front()) == CLASS::BLC );                                \
            __quex_assert(*(BASE::_memory.back())  == CLASS::BLC );                                \
            if( _end_of_file_p == 0x0 ) {                                                    \
                __quex_assert(BASE::_input_p      <= BASE::_memory.back());                            \
                __quex_assert(_lexeme_start_p <= BASE::_memory.back());                            \
            } else {                                                                         \
                __quex_assert(BASE::_input_p      <= _end_of_file_p);                            \
                __quex_assert(_lexeme_start_p <= _end_of_file_p);                            \
                /**/                                                                         \
                __quex_assert(_end_of_file_p  >= content_front());                           \
                __quex_assert(_end_of_file_p  <= BASE::_memory.back());                            \
                /**/                                                                         \
                __quex_assert(*_end_of_file_p == CLASS::BLC);                                \
            }                                                                                \
        }
#   else
#      define  QUEX_BUFFER_ASSERT_CONSISTENCY()  /* empty */
#   endif

#   if defined(__QUEX_OPTION_UNIT_TEST) && defined(__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS)
#      define QUEX_BUFFER_SHOW_BUFFER_LOAD(InfoStr)   \
        {                                 \
            std::cout << InfoStr << "\n"; \
            show_content();               \
        }
#   else
#      define QUEX_BUFFER_SHOW_BUFFER_LOAD(InfoStr) /* empty */
#   endif

    TEMPLATE_IN
    CLASS::Buffer(FixedSizeCharacterStream<CharacterCarrierType>* _input_strategy, 
                  size_t               BufferSize   /* = 65536 */, 
                  CharacterCarrierType Value_BLC    /* = DEFAULT_BUFFER_LIMIT_CODE */)
    : BLC(Value_BLC)
    {
        __constructor_core(_input_strategy, 0x0, BufferSize);
    }

    TEMPLATE_IN 
    CLASS::Buffer(FixedSizeCharacterStream<CharacterCarrierType>* _input_strategy, 
                  CharacterCarrierType* memory_chunk,
                  size_t                ChunkSize, 
                  CharacterCarrierType  Value_BLC     /* = DEFAULT_BUFFER_LIMIT_CODE */)
    : BLC(Value_BLC)
    {
        __constructor_core(_input_strategy, memory_chunk, ChunkSize);
    }
                  

    TEMPLATE_IN void  
    CLASS::__constructor_core(FixedSizeCharacterStream<CharacterCarrierType>* _input_strategy, 
                              CharacterCarrierType* buffer_memory, size_t BufferSize) 
    {
        __quex_assert(BufferSize > 2); 
        __quex_assert(MinFallBackN < BufferSize - 2);  // '-2' because of the border chars.
        //___________________________________________________________________________
        //
        // NOTE: The borders are filled with buffer limit codes. Thus, the
        //       buffer's volume is two elements greater then the buffer's content.
        QuexBufferCore_init(this, buffer_memory, BufferSize, BLC);

        // -- for a later 'map_to_stream_position(character_index), the strategy might
        //    have some plans.
        _input = _input_strategy;
        _input->register_begin_of_file();

        // -- load initial content starting from position zero
        const size_t LoadedN = _input->load_backward(this);
        __quex_assert(LoadedN <= Buffer_content_size(this));

        // -- function pointer for overflow handling
        _on_overflow = 0x0;
        // TODO: on_overflow = default_memory_on_overflow_handler<CharacterCarrierType>;

        QUEX_BUFFER_ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN CLASS::~Buffer() 
    {
        // if buffer was provided from outside, then we should better not delete it
        if( BASE::_memory._external_owner_f ) return;

        delete [] BASE::_memory._front; 
    }

    TEMPLATE_IN  int CLASS::load_forward() 
    {
        _input->load_forward(this);
    }

    TEMPLATE_IN  int  CLASS::load_backward() 
    {
        _input->load_backward(this);
    }

#if 0
    TEMPLATE_IN  void CLASS::move_forward(const size_t Distance)
        // NOTE: This function is not to be called during the lexical analyzer process
        //       They should only be called by the user during pattern actions.
    {
        // Assume: The distance is mostly small with respect to the buffer size, so 
        // that one buffer load ahead is sufficient for most cases. In cases that this
        // does not hold it loads the buffer contents stepwise. A direct jump to more
        // then one load ahead would require a different load function. Please, consider
        // that different input strategies might rely on dynamic character length codings
        // 
        size_t remaining_distance_to_target = Distance;
        while( 1 + 1 == 2 ) {
            QUEX_BUFFER_ASSERT_CONSISTENCY();
            if( _end_of_file_p != 0x0 ) {
                if( _input_p + remaining_distance_to_target >= _end_of_file_p ) {
                    _input_p      = _end_of_file_p;
                    _lexeme_start_p = _input_p;
                    QUEX_BUFFER_ASSERT_CONSISTENCY();
                    return;
                } 
            } else {
                if( _input_p + remaining_distance_to_target < BASE::_memory.back() ) {
                    _input_p      += remaining_distance_to_target;
                    _lexeme_start_p  = _input_p + 1;
                    QUEX_BUFFER_ASSERT_CONSISTENCY();
                    return;
                }
            }

            // move current_p to end of the buffer, thus decrease the remaining distance
            remaining_distance_to_target -= (BASE::_memory.back() - _input_p);
            _input_p      = BASE::_memory.back();
            _lexeme_start_p = BASE::_memory.back();

            // load subsequent segment into buffer
            load_forward();
            QUEX_BUFFER_ASSERT_CONSISTENCY();
        }
    }

    TEMPLATE_IN  void CLASS::move_backward(const size_t Distance)
        // NOTE: This function is not to be called during the lexical analyzer process
        //       They should only be called by the user during pattern actions.
    {
        // Assume: The distance is mostly small with respect to the buffer size, so 
        // that one buffer load ahead is sufficient for most cases. In cases that this
        // does not hold it loads the buffer contents stepwise. A direct jump to more
        // then one load ahead would require a different load function. Please, consider
        // that different input strategies might rely on dynamic character length codings.
        size_t remaining_distance_to_target = Distance;
        while( 1 + 1 == 2 ) {
            QUEX_BUFFER_ASSERT_CONSISTENCY();
            if( _input_p - remaining_distance_to_target <= content_front() ) {
                if( *(BASE::_memory.front()) == CLASS::BLC ) {
                    _input_p      = content_front();
                    _lexeme_start_p = content_front() + 1; 
                    QUEX_BUFFER_ASSERT_CONSISTENCY();
                    return;
                }
            }
            // move current_p to begin of the buffer, thus decrease the remaining distance
            remaining_distance_to_target -= (_input_p - content_front());
            _input_p      = content_front();
            _lexeme_start_p = content_front() + 1;

            load_backward();
        }
    }
#endif

    TEMPLATE_IN  void CLASS::_reset()
    {
        // Reload the 'front' of the file into the 'front'!
        // ALWAYS! --- independent of current position! This is so, since the
        // __constructor_core() will set the 'base' to the current input position
        // of the stream.
        _input->seek_begin_of_file();

        // What happens here is exactly the same as when constructing a new
        // buffer with a given bunch of memory (the currently used one). Then
        // however, one needs to set the flag 'external memory' according to
        // what it was before.
        const bool Tmp = BASE::_memory._external_owner_f;
        CLASS::__constructor_core(_input, 
                                  BASE::_memory._front, BufferMemory_size(this));
        BASE::_memory._external_owner_f = Tmp;
    }

#undef TEMPLATE_IN
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
