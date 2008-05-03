// : -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2007 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_

#include <quex/code_base/buffer/input_strategy>

#include <iostream>

#include <cassert>
extern "C" {
#include <quex/code_base/compatibility/inttypes.h>
}
#include<cstdlib>
#include<cstring>

namespace quex {

#   define TEMPLATE template<class CharacterType>
#   define CLASS    buffer_core<CharacterType>   

    TEMPLATE inline CLASS::buffer_core(size_t           BufferSz        /*=65536*/, 
                                       size_t           BackupSectionSz /*=64*/,
                                       character_type   Value_BLC       /*=Default ...*/)
    {
    //________________________________________________________________________________
    // NOTE: With the forward/backward behavior implemented below it is
    //       **always** safe to say that the character which they return is
    //       the character underneath '_current_p'. This significantly simplfies
    //       the discussion about possible use-cases.
    // NOTE: Limit codes are stored at the end of the buffer. This causes
    //       all transitions to fail in the state machine. The 'fail'
    //       case has now to check wether the current input is BLC.
    //       If so, the load_new_content() function is to be called.
    // THUS: Under normal conditions (99.99% of the cases) no extra
    //       check for end of buffer is necessary => speed up.
    TEMPLATE inline int CLASS::get_forward()  { ASSERT_CONSISTENCY(); return *(++_current_p); }
    TEMPLATE inline int CLASS::get_backward() { ASSERT_CONSISTENCY(); return *(--_current_p); }

    TEMPLATE void              
        CLASS::set_subsequent_character(const int Value) {
            ASSERT_CONSISTENCY();
            *(_current_p + 1) = Value;
        }

    TEMPLATE typename CLASS::character_type    
        CLASS::get_subsequent_character() { 
            ASSERT_CONSISTENCY();
            return *(_current_p + 1); 
        }

    TEMPLATE typename CLASS::character_type    
        CLASS::get_current_character() { 
            ASSERT_CONSISTENCY();
            return *_current_p; 
        }

    TEMPLATE void       
        CLASS::mark_lexeme_start() { 
            _lexeme_start_p = _current_p + 1;  // pointing to the next character to be read   
            ASSERT_CONSISTENCY();
        }

    TEMPLATE void 
        CLASS::set_current_p(character_type* Adr) 
        { 
            _current_p = Adr;
            ASSERT_CONSISTENCY();
        }

    TEMPLATE inline void 
        CLASS::__end_of_file_set(character_type* EOF_p)
        {
            _end_of_file_p  = EOF_p; 
            *_end_of_file_p = buffer_core::BLC; 
            ASSERT_CONSISTENCY();
        }

    TEMPLATE inline void 
        CLASS::__end_of_file_unset()
        {
            _end_of_file_p   = 0x0; 
            ASSERT_CONSISTENCY();
        }


    TEMPLATE inline typename CLASS::character_type*    
        CLASS::get_lexeme_start_p()
        {
            ASSERT_CONSISTENCY();
            return _lexeme_start_p;
        }

    TEMPLATE inline typename CLASS::memory_position    
        CLASS::tell_adr()
        {
            ASSERT_CONSISTENCY();
#           ifndef QUEX_OPTION_ACTIVATE_ASSERTS
            const long begin_pos = (long)(_input.map_to_stream_position(this->_character_index_at_front));
            return memory_position(_current_p, begin_pos);
#           else
            return memory_position(_current_p);
#           endif
        }

    TEMPLATE inline void 
        CLASS::seek_adr(const memory_position Adr)
        {
#           ifndef QUEX_OPTION_ACTIVATE_ASSERTS
            // Check wether the memory_position is relative to the current start position 
            // of the stream. That means, that the tell_adr() command was called on the
            // same buffer setting or the positions have been adapted using the += operator.
            const long begin_pos = (long)(_input.map_to_stream_position(this->_character_index_at_front));
            __quex_assert(Adr.buffer_start_position == begin_pos);
            _current_p = Adr.address;
#           else
            _current_p = Adr;
#           endif
            ASSERT_CONSISTENCY();
        }

    TEMPLATE inline void 
        CLASS::seek_offset(const int Offset)
        {
            _current_p += Offset;

            ASSERT_CONSISTENCY();
        }

    TEMPLATE inline void              
        CLASS::move_forward(const size_t Distance)
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
                ASSERT_CONSISTENCY();
                if( _end_of_file_p != 0x0 ) {
                    if( _current_p + remaining_distance_to_target >= _end_of_file_p ) {
                        _current_p      = _end_of_file_p;
                        _lexeme_start_p = _current_p;
                        ASSERT_CONSISTENCY();
                        return;
                    } 
                } else {
                    if( _current_p + remaining_distance_to_target < _buffer.back() ) {
                        _current_p      += remaining_distance_to_target;
                        _lexeme_start_p  = _current_p + 1;
                        ASSERT_CONSISTENCY();
                        return;
                    }
                }

                // move current_p to end of the buffer, thus decrease the remaining distance
                remaining_distance_to_target -= (_buffer.back() - _current_p);
                _current_p      = _buffer.back();
                _lexeme_start_p = _buffer.back();

                // load subsequent segment into buffer
                load_forward();
                ASSERT_CONSISTENCY();
            }
        }

    TEMPLATE inline void
        CLASS::move_backward(const size_t Distance)
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
                ASSERT_CONSISTENCY();
                if( _current_p - remaining_distance_to_target <= content_front() ) {
                    if( _buffer[0] == BLC ) {
                        _current_p      = _buffer;
                        _lexeme_start_p = _current_p + 1; 
                        ASSERT_CONSISTENCY();
                        return;
                    }
                }
                // move current_p to begin of the buffer, thus decrease the remaining distance
                remaining_distance_to_target -= (_current_p - content_front());
                _current_p      = content_front();
                _lexeme_start_p = content_front() + 1;

                load_backward();
            }
        }

#undef TEMPLATE
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_
