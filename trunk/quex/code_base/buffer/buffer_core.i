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
        : BLC(Value_BLC), BUFFER_SIZE(BufferSz), FALLBACK_N(BackupSectionSz)
    {
        __quex_assert(BUFFER_SIZE > 2); 
        __quex_assert(FALLBACK_N < BUFFER_SIZE - 2);  // '-2' because of the border chars.
        //___________________________________________________________________________
        //
        // NOTE: The borders are filled with buffer limit codes, end of file or
        //       begin of file codes. Thus the buffer's volume is two elements greater
        //       then the buffer's content.
        //
        _buffer = new character_type[BUFFER_SIZE];      
        // _buffer[0]             = lower buffer limit code character
        // _buffer[1]             = first char of content
        // _buffer[BUFFER_SIZE-2] = last char of content
        // _buffer[BUFFER_SIZE-1] = upper buffer limit code character

        // -- current = 1 before content, 
        //    because we always read '_current_p + 1' as next char.
        _current_p      = _buffer;     
        // -- initial lexeme start, of course, at the start
        _lexeme_start_p = _buffer + 1;

    }

    TEMPLATE inline
        CLASS::~buffer_core() {
            delete [] _buffer;
        }

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
    TEMPLATE inline int  CLASS::get_forward() {
            __quex_assert(_current_p >= buffer_begin());
            __quex_assert(_current_p <  buffer_end());
            return *(++_current_p);
        }

    TEMPLATE inline int  CLASS::get_backward() {
            __quex_assert(_current_p >= buffer_begin());
            __quex_assert(_current_p <  buffer_end());
            return *(--current_p); 
        }

    TEMPLATE void              
        CLASS::set_subsequent_character(const int Value) {
            __quex_assert(_current_p > _buffer );
            __quex_assert(_current_p < _buffer + 1 + content_size());
            *(_current_p + 1) = Value;
        }

    TEMPLATE typename CLASS::character_type    
        CLASS::get_subsequent_character() { 
            __quex_assert(_current_p >= content_begin());
            __quex_assert(_current_p < content_end());
            return *(_current_p + 1); 
        }

    TEMPLATE typename CLASS::character_type    
        CLASS::get_current_character() { 
            __quex_assert(_current_p >= content_begin());
            __quex_assert(_current_p < content_end());
            return *_current_p; 
        }

    TEMPLATE void       
        CLASS::mark_lexeme_start() { 
            // allow: *_current_p = BLC
            __quex_assert(_current_p >= content_begin() - 2);                
            __quex_assert(_end_of_file_p != 0x0 || _current_p < content_end());  
            __quex_assert(_end_of_file_p == 0x0 || _current_p <= _end_of_file_p);  

            // pointing to the next character to be read
            _lexeme_start_p = _current_p + 1;     
        }

    TEMPLATE void 
        CLASS::set_current_p(character_type* Adr) 
        { 
            _current_p = Adr;
            EMPTY_or_assert_consistency();
        }

    TEMPLATE inline void 
        CLASS::__set_end_of_file(character_type* EOF_p)
        {
            _end_of_file_p  = EOF_p; 
            *_end_of_file_p = buffer_core::BLC; // buffer_core::EOFC;
        }

    TEMPLATE inline void 
        CLASS::__unset_end_of_file()
        {
            _end_of_file_p  = 0x0; 
            *(content_end()) = buffer_core::BLC;
        }

    TEMPLATE inline void 
        CLASS::__set_begin_of_file()
        {
            *(buffer_begin()) = buffer_core::BLC; // buffer_core::BOFC; 
        }

    TEMPLATE inline void 
        CLASS::__unset_begin_of_file()
        {
            *(buffer_begin()) = buffer_core::BLC; 
        }

    TEMPLATE inline typename CLASS::character_type*    
        CLASS::get_lexeme_start_p()
        {
            EMPTY_or_assert_consistency();
            return _lexeme_start_p;
        }

    TEMPLATE inline typename CLASS::memory_position    
        CLASS::tell_adr()
        {
            EMPTY_or_assert_consistency();
#ifndef NDEBUG
            return memory_position(_current_p, DEBUG_get_start_position_of_buffer());
#else
            return memory_position(_current_p);
#endif
        }

    TEMPLATE inline void 
        CLASS::seek_adr(const memory_position Adr)
        {
#ifndef NDEBUG
            // Check wether the memory_position is relative to the current start position 
            // of the stream. That means, that the tell_adr() command was called on the
            // same buffer setting or the positions have been adapted using the += operator.
            __quex_assert(Adr.buffer_start_position == DEBUG_get_start_position_of_buffer());
            _current_p = Adr.address;
#else
            _current_p = Adr;
#endif
            EMPTY_or_assert_consistency();
        }

    TEMPLATE inline void 
        CLASS::seek_offset(const int Offset)
        {
            _current_p += Offset;

            EMPTY_or_assert_consistency();
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
            __quex_assert(_current_p >= buffer_begin() - 1);
            __quex_assert(_current_p <  buffer_end()   - 1);
            // 
            size_t remaining_distance_to_target = Distance;
            while( 1 + 1 == 2 ) {
                if( _end_of_file_p != 0x0 ) {
                    if( _current_p + remaining_distance_to_target >= _end_of_file_p ) {
                        _current_p      = _end_of_file_p;
                        _lexeme_start_p = _current_p;
                        return;
                    } 
                } else {
                    if( _current_p + remaining_distance_to_target < content_end() ) {
                        _current_p      += remaining_distance_to_target;
                        _lexeme_start_p  = _current_p + 1;
                        return;
                    }
                }

                // move current_p to end of the buffer, thus decrease the remaining distance
                remaining_distance_to_target -= (content_end() - _current_p);
                _current_p      = content_end();
                _lexeme_start_p = content_end();  // safe not to hit asserts (?)

                // load subsequent segment into buffer
                load_forward();
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
            __quex_assert(_current_p >= buffer_begin());
            __quex_assert(_current_p <  buffer_end());
            // 
            size_t remaining_distance_to_target = Distance;
            while( 1 + 1 == 2 ) {
                if( _current_p - remaining_distance_to_target <= content_begin() ) {
                    if( _buffer[0] == BLC ) {
                        _current_p      = _buffer;
                        _lexeme_start_p = _current_p + 1; 
                        return;
                    }
                }
                // move current_p to begin of the buffer, thus decrease the remaining distance
                remaining_distance_to_target -= (_current_p - content_begin());
                _current_p      = content_begin();
                _lexeme_start_p = content_begin() + 1;

                load_backward();
            }
        }


#if ( defined(NDEBUG) && ! defined(__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER) )
    TEMPLATE void CLASS::EMPTY_or_assert_consistency(bool AllowTerminatingZeroF /* = true */) {}
#else
    TEMPLATE void 
        CLASS::EMPTY_or_assert_consistency(bool AllowTerminatingZeroF /* = true */) {
#           ifdef QUEX_OPTION_ACTIVATE_ASSERTS
            const int LexemeStartOffSet = _lexeme_start_p - content_begin();
#           endif
            // NOTE: If NDEBUG is defined, the following asserts are taken out
            //       and this function is a null function that is deleted by the compiler.
            // NOTE: No assumptions can be made in general on the relation between
            //       _current_p and _lexeme_start_p, since for forwards lexing
            //       _current_p comes before _lexeme_start_p, wherelse for back-
            //       ward lexing this is vice versa. 
            //       See "code_base/core_engine/definitions-quex-buffer.h"
            if( _lexeme_start_p < buffer_begin() )    std::abort();                
            __quex_assert(LexemeStartOffSet >= -1);
            //
            if( _current_p < buffer_begin() - 1) std::abort(); 
            __quex_assert(*(buffer_begin()) == buffer_core::BOFC || *(buffer_begin()) == buffer_core::BLC);   
            //
            if( _end_of_file_p == 0x0 ) {
                __quex_assert(_current_p  <=  buffer_end()); 
                __quex_assert(_lexeme_start_p < buffer_end());
                /* NOTE: These asserts go back to a time where there where different delimiters
                 *       for 'begin of file', 'end of file', and 'buffer limit'.
                 *
                 * if( AllowTerminatingZeroF ) {
                 *   __quex_assert(    *(content_end()) == buffer_core::EOFC   // content_end -> 1st character after
                 *           || *(content_end()) == buffer_core::BLC    // the last character of content.
                 *           || *(content_end()) == character_type(0));  
                 * } else {
                 *   __quex_assert(    *(content_end()) == buffer_core::EOFC   // content_end -> 1st character after
                 *                  || *(content_end()) == buffer_core::BLC);  // the last character of content.
                 *}
                 */
                // NOTE: strange '+1' because: 
                //         -- LexemeStartOffSet == -1 is ok and 
                //         -- size_t might be and unsigned type.
                __quex_assert((size_t)(LexemeStartOffSet + 1) <= content_size() + 1); 
            } else {
                __quex_assert(_end_of_file_p  >= content_begin());
                __quex_assert(_end_of_file_p  < content_end());
                __quex_assert(_lexeme_start_p <= _end_of_file_p);  
                __quex_assert(_current_p      <= _end_of_file_p); 
                /* NOTE: These asserts go back to a time where there where different delimiters
                 *       for 'begin of file', 'end of file', and 'buffer limit'.
                 *
                 * if( AllowTerminatingZeroF ) 
                 *   __quex_assert(   *_end_of_file_p == buffer_core::EOFC
                 *                 || *_end_of_file_p == character_type(0));  
                 * else                        
                 *   __quex_assert(*_end_of_file_p == buffer_core::EOFC);
                 */ 
                __quex_assert(LexemeStartOffSet <= _end_of_file_p - content_begin());
            }
        }
#endif



#ifdef __QUEX_OPTION_UNIT_TEST
    TEMPLATE inline typename CLASS::character_type  
        CLASS::get_border_char(const character_type* C) {
            if( *C != buffer_core::BLC ) { 
                std::cout << "BLC = " << (int)(*C) << " " << int(buffer_core::BLC) << std::endl; 
                return '?'; 
            }
            else if( C == this->_end_of_file_p )                                             return ']';
            else if( this->DEBUG_get_start_position_of_buffer() == 0 && C == this->_buffer ) return '[';
            return '|';
        }

    // Do not forget to include <iostream> before this header when doing those unit tests
    // which are using this function.
    TEMPLATE inline void  
        CLASS::show_content() {
            // NOTE: if the limiting char needs to be replaced temporarily by
            //       a terminating zero.
            // NOTE: this is a **simple** printing function for unit testing and debugging
            //       it is thought to print only ASCII characters (i.e. code points < 0xFF)
            int              covered_char = 0xFFFF;
            character_type*  end_p = 0x0;

            for(end_p = content_begin(); end_p < buffer_end() ; ++end_p) {
                if( end_p == _end_of_file_p || *end_p == buffer_core::BLC ) { break; }
            }
            //_________________________________________________________________________________
            char tmp[content_size()+4];
            // tmp[0]                  = outer border
            // tmp[1]                  = buffer limit
            // tmp[2...content_size()+1] = content_begin()[0...content_size()-1]
            // tmp[content_size()+2]     = buffer limit
            // tmp[content_size()+3]     = outer border
            // tmp[content_size()+4]     = terminating zero
            for(size_t i=2; i<content_size()+2; ++i) tmp[i] = ' ';
            tmp[content_size()+4] = '\0';
            tmp[content_size()+3] = '|';
            tmp[content_size()+2] = get_border_char(content_end());
            tmp[1]                = get_border_char(content_begin()-1);
            tmp[0]                = '|';
            //
            tmp[_current_fallback_n - 1 + 2]      = ':';        
            tmp[_current_p - content_begin() + 2] = 'C';
            if( _lexeme_start_p >= content_begin() && _lexeme_start_p <= content_end() ) 
                tmp[(int)(_lexeme_start_p - content_begin()) + 2] = 'S';
            //
            if ( _current_p == content_begin() - 2 ) {
                std::cout << tmp << " <out>";
            } else {
                std::cout << tmp << " ";
                if( *_current_p == buffer_core::BLC ) std::cout << "BLC";
                else                                  std::cout << "'" << *_current_p << "'";
            }
            // std::cout << " = 0x" << std::hex << int(*_current_p) << std::dec 
            std::cout << std::endl;
            std::cout << "|" << get_border_char(buffer_begin());
            for(character_type* iterator = content_begin(); iterator != end_p; ++iterator) {
                std::cout << *iterator;
            }
            std::cout << get_border_char(end_p);
            //
            const size_t L = _end_of_file_p == 0x0 ? 0 : content_end() - _end_of_file_p;
            for(size_t i=0; i < L; ++i) std::cout << "|";

            std::cout << "|\n";
        }


#endif

#undef TEMPLATE
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_
