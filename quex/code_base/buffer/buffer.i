// : -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2007 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_

#include <quex/code_base/buffer/input_strategy>

namespace quex {
#   define TEMPLATE_IN  template<class CharacterCarrierType> inline
#   define CLASS        buffer<CharacterCarrierType>   

    TEMPLATE_IN 
        CLASS::buffer(input_strategy<CharacterCarrierType>* _input_strategy, 
               size_t BufferSize /* = 65536 */, size_t BackupSectionSize /* = 64 */,
               character_type Value_BLC  /* = DEFAULT_BUFFER_LIMIT_CODE */)
        : BLC(Value_BLC)
    {
        __constructor_core(_input_strategy, 0x0, BufferSize, BackupSectionSize);
    }
                  

    TEMPLATE_IN  void  
        CLASS::__constructor_core(input_strategy<CharacterCarrierType>* _input_strategy, 
                                  CharacterCarrierType* buffer_memory, size_t BufferSize, 
                                  size_t FallBackN) 
    {
        __quex_assert(BufferSize > 2); 
        __quex_assert(FallBackN < BufferSize - 2);  // '-2' because of the border chars.
        //___________________________________________________________________________
        //
        // NOTE: The borders are filled with buffer limit codes. Thus, the
        // buffer's volume is two elements greater then the buffer's content.
        //
        if( buffer_memory == 0x0 ) {
            _buffer._front            = new character_type[BufferSize];      
            _buffer._external_owner_f = false;
        }
        else {
            _buffer._front            = buffer_memory;
            _buffer._external_owner_f = true;
        }
        _buffer._back = _buffer._front + BufferSize - 1;

        // _buffer[0]             = lower buffer limit code character
        // _buffer[1]             = first char of content
        // _buffer[BUFFER_SIZE-2] = last char of content
        // _buffer[BUFFER_SIZE-1] = upper buffer limit code character
        *(_buffer._front) = CLASS::BLC; // set buffer limit code
        *(_buffer._back)  = CLASS::BLC; // set buffer limit code

        // -- current = 1 before content, 
        //    because we always read '_current_p + 1' as next char.
        _current_p      = _buffer.front();     
        // -- initial lexeme start, of course, at the start
        _lexeme_start_p = content_front();

        // -- for a later 'map_to_stream_position(character_index), the strategy might
        //    have some plans.
        _input = _input_strategy;
        _input->register_begin_of_file();

        // -- load initial content starting from position zero
        const size_t LoadedN = _input->read_characters(content_front(), content_size());
        __quex_assert(LoadedN <= content_size());

        _character_index_at_front = 0;

#       ifdef __QUEX_OPTION_UNIT_TEST
        _SHOW_current_fallback_n = FallBackN; // onyl used for 'show'
#       endif

        // -- end of file / end of buffer:
        if( LoadedN != content_size() ) 
            __end_of_file_set(content_front() + LoadedN); // end of file
        else
            __end_of_file_unset();                        // buffer limit

        // -- function pointer for overflow handling
        // TODO: on_overflow = default_buffer_on_overflow_handler<CharacterCarrierType>;

        ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN CLASS::~buffer() 
    {
        // if buffer was provided from outside, then we should better not delete it
        if( _buffer._external_owner_f ) return;

        delete [] _buffer._front; 
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
    TEMPLATE_IN  int CLASS::get_forward()  { ASSERT_CONSISTENCY(); return *(++_current_p); }
    TEMPLATE_IN  int CLASS::get_backward() { ASSERT_CONSISTENCY(); return *(--_current_p); }

    TEMPLATE_IN  int CLASS::load_forward() 
    {
        // PURPOSE: This function is to be called as a reaction to a buffer limit code 'BLC'
        //          as returned by 'get_forward()'. Its task is to load new content into the 
        //          buffer such that 'get_forward() can continue iterating. This means that the 
        //          '_current_p' points to one of the following positions:
        //
        //          (1) Beginning of the Buffer: In this case, no reload needs to take place.
        //              It can basically only appear if 'load_forward()' is called after
        //              'get_backward()'---and this does not make sense. But returning a '0'
        //              (which is >= 0 and indicates that everything is ok) tells the application 
        //              that nothing has been loaded, and the next 'get_forward()' will work 
        //              normally.
        //
        //          (2) End of File Pointer: (which may be equal to the end of the buffer) 
        //              In this case no further content can be loaded. The function returns '-1'.
        //
        //          (3) End of Buffer (if it is != End of File Pointer): Here a 'normal' load of
        //              new data into the buffer can happen.
        //
        // RETURNS: '>= 0'   number of characters that were loaded forward in the stream.
        //          '-1'     if forward loading was not possible (end of file)
        SHOW_BUFFER_LOAD("LOAD FORWARD(entry)");

        // (*) Check for the three possibilities mentioned above
        if     ( _current_p == _buffer.front() ) { return 0; }       // (1)
        else if( _current_p == _end_of_file_p )  { return -1; }      // (2)
        else if( _current_p != _buffer.back() ) {                     
            throw std::range_error("Inaddmissible 'BufferLimitCode' character appeared in input stream.\n" 
                                   "(Check character encoding)");  
        }
        //                                                           // (3)

        //
        // HERE: current_p == END OF THE BUFFER!
        // 

        // (*) Double check on consistency
        //     -- 'load_forward()' should only be called, if the '_current_p' reached a border.
        //        Since we know from above, that we did not reach end of file, it can be assumed
        //        that the _end_of_file_p == 0x0 (buffer does not contain EOF).
        __quex_assert(_end_of_file_p == 0x0);
        ASSERT_CONSISTENCY();

        //___________________________________________________________________________________
        // (1) Fallback: A certain region of the current buffer is copied in front such that
        //               if necessary the stream can go backwards without a backward load.
        //
        //                            fallback_n
        //                               :
        //                |11111111111111:22222222222222222222222222222222222222|
        //                  copy of      :   new loaded content of buffer
        //                  end of old   
        //                  buffer      
        //
        //     The fallback region is related to the lexeme start pointer. The lexeme start 
        //     pointer always needs to lie inside the buffer, because applications might read
        //     their characters from it. The 'stretch' [lexeme start, current_p] must be 
        //     contained in the new buffer (precisely in the fallback region).
        __quex_assert(_current_p >= _lexeme_start_p);
        const int MinFallbackN = _current_p - _lexeme_start_p;

        // (*) Fallback region = max(default size, necessary size)
        const int FallBackN = _buffer.default_fallback_n() > MinFallbackN ? 
                              _buffer.default_fallback_n() : MinFallbackN;

        // (*) Copy fallback region
        //     If there is no 'overlap' from source and drain than the faster memcpy() can 
        //     used instead of memmove().
        character_type*  source = content_back() - FallBackN + 1;
        character_type*  drain  = content_front();
        if( drain + FallBackN >= source  ) {
            std::memmove(drain, source, FallBackN * sizeof(character_type));
        } else { 
            std::memcpy(drain, source, FallBackN * sizeof(character_type));
        }
#       ifdef __QUEX_OPTION_UNIT_TEST
        _SHOW_current_fallback_n = FallBackN; // onyl used for 'show'
#       endif

        //___________________________________________________________________________________
        // (2) Load new content
        //
        // The input_strategy emulates a stream of characters of constant width, independtly 
        // of the character coding that is used. Thus, it is safe to compute the position at the
        // end of the buffer by simple addition of 'content size' to '_character_index_at_front'.
        //
        const int CharacterIndexAtEnd = _character_index_at_front + content_size();
        if( _input->tell_character_index() != CharacterIndexAtEnd  ) { 
            _input->seek_character_index(CharacterIndexAtEnd);
        }

        const size_t    LoadN = content_size() - FallBackN;
        // (*) If more characters need to be loaded than the buffer can hold,
        //     then this is a critical overflow. Example: If lexeme extends over 
        //     the whole buffer (==> MinFallbackN >= content_size).
        if( LoadN == 0 ) { if( on_overflow(this, /* ForwardF */true) == false) return -1; }

        character_type* new_content = content_front() + FallBackN;
        const size_t    LoadedN     = _input->read_characters(new_content, LoadN);

        //     If end of file has been reached, then the 'end of file' pointer needs to be set
        if( LoadedN != LoadN ) __end_of_file_set(content_front() + FallBackN + LoadedN);
        else                   __end_of_file_unset();

        _character_index_at_front += LoadN - FallBackN;

        //___________________________________________________________________________________
        // (3) Pointer adaption
        //     Next char to be read: '_current_p + 1'
        _current_p      = content_front() + FallBackN - 1;   
        //     MinFallbackN = distance from '_lexeme_start_p' to '_current_p'
        _lexeme_start_p = _current_p - MinFallbackN; 

        SHOW_BUFFER_LOAD("LOAD FORWARD(exit)");
        ASSERT_CONSISTENCY();
        // NOTE: Return value used for adaptions of memory addresses. The same rule as for
        //       _lexeme_start_p holds for those addresses.
        return LoadN;
    }

    TEMPLATE_IN  int  CLASS::load_backward() 
    {
        // PURPOSE: This function is to be called as a reaction to a buffer limit code 'BLC'
        //          as returned by 'get_backward()'. Its task is the same as the one of 
        //          'load_forward()'--only in opposite direction. Here only two cases need 
        //          to be distinguished. The current_p points to 
        //
        //          (1) End of Buffer or End of File pointer: No backward load needs to 
        //              happen. This can only occur if a 'get_forward()' was called right
        //              before.
        //
        //          (2) Begin of the buffer and the buffer is the 'start buffer':
        //              in this case no backward load can happen, because we are at the 
        //              beginning. The function returns -1.
        //
        //          (3) Begin of buffer and _begin_of_file_f is not set!: This is the case
        //              where this function, actually, has some work to do. It loads the
        //              buffer with 'earlier' content from the file.
        //
        //
        // RETURNS: Distance that was loaded backwards.
        //          -1 in case of backward loading is not possible (begin of file)
        //     
        // COMMENT: 
        //     
        // For normal cases the fallback region, i.e. the 'FALLBACK_N' buffer bytes 
        // allows to go a certain distance backwards immediately. If still the begin 
        // of the buffer is reached, then this is an indication that something is
        // 'off-the-norm'. Lexical analysis is not supposed to go longtimes
        // backwards. For such cases we step a long stretch backwards: A
        // THIRD of the buffer's size! 
        //
        // A meaningful fallback_n would be 64 Bytes. If the buffer's size
        // is for example 512 kB then the backwards_distance of A THIRD means 170
        // kB. This leaves a  safety region which is about 2730 times
        // greater than normal (64 Bytes). After all, lexical analysis means
        // to go **mainly forward** and not backwards.
        //
        SHOW_BUFFER_LOAD("LOAD BACKWARD(entry)");
        ASSERT_CONSISTENCY();

        // (*) Check for the three possibilities mentioned above
        if     ( _current_p == _buffer.back() )  { return 0; }   // (1)
        else if( _current_p == _end_of_file_p )  { return 0; }   // (1)
        else if( _current_p != _buffer.front() ) {
            throw std::range_error("Inaddmissible 'BufferLimit' character code appeared in input stream.\n" 
                                   "(Check character encoding)");  
        }
        else if( _character_index_at_front == 0 ) { return -1; } // (2)
        //                                                       // (3)
        // HERE: current_p == FRONT OF THE BUFFER!
        //

        //_______________________________________________________________________________
        // (1) Compute distance to go backwards
        //
        //     We need to make sure, that the lexeme start pointer remains inside the
        //     buffer, so that we do not loose the reference. From current_p == buffer begin
        //     it is safe to say that _lexeme_start_p > _current_p (the lexeme starts
        //     on a letter not the buffer limit).
        __quex_assert(_lexeme_start_p > _current_p);
        const int IntendedBackwardDistance = (int)(content_size() / 3);   

        //     Before:    |C      L                  |
        //
        //     After:     |       C      L           |
        //                 ------->
        //                 backward distance
        //
        //     Lexeme start pointer L shall lie inside the buffer. Thus, it is required:
        //
        //               backward distance + (C - L) < size
        //           =>            backward distance < size - (C - L)
        //          
        if( _lexeme_start_p == content_back() ) {
            if( on_overflow(this, /* ForwardF */false) == false ) return -1;
        }
        const int MaxBackwardDistance =   content_size() 
            - (int)(_lexeme_start_p - _current_p);
        const int BackwardDistance = IntendedBackwardDistance > MaxBackwardDistance ? 
            MaxBackwardDistance : IntendedBackwardDistance;

        //_______________________________________________________________________________
        // (2) Compute the stream position of the 'start to read' 
        //
        // It is not safe to assume that the character size is fixed. Thus it is up to
        // the input strategy to determine the input position that belongs to a character
        // position.
        int start_character_index = _character_index_at_front - BackwardDistance;
        if( start_character_index < 0 ) start_character_index = 0;

        // (*) copy content that is already there to its new position.
        //     (copying is much faster then loading new content from file)
        std::memmove(content_front() + BackwardDistance,
                     content_front(), content_size() - BackwardDistance);

        //_______________________________________________________________________________
        // (3) Load content
        //
        _input->seek_character_index(start_character_index);
#           ifdef QUEX_OPTION_ACTIVATE_ASSERTS
        const size_t LoadedN = // avoid unused variable in case '__quex_assert()' is deactivated
#           endif
            _input->read_characters(content_front(), BackwardDistance);
        // -- If file content < buffer size, then the start position of the stream to which
        //    the buffer refers is always 0 and no backward loading will ever happen.
        // -- If the file content >= buffer size, then backward loading must always fill
        //    the buffer. 
        __quex_assert(LoadedN == (size_t)BackwardDistance);

        _input->read_characters(content_front(), BackwardDistance);

        // -- end of file / end of buffer:
        if( _end_of_file_p ) {
            character_type*   NewEndOfFileP = _end_of_file_p + BackwardDistance;
            if( NewEndOfFileP < _buffer.back() ) __end_of_file_set(NewEndOfFileP);
            else                                 __end_of_file_unset();
        }
        // -- character index of begin of buffer = where we started reading new content
        _character_index_at_front = start_character_index;

        //________________________________________________________________________________
        // (4) Adapt pointers
        //
        _current_p      += BackwardDistance + 1; 
        _lexeme_start_p += BackwardDistance;

        SHOW_BUFFER_LOAD("LOAD BACKWARD(exit)");
        ASSERT_CONSISTENCY();
        return BackwardDistance;
    }

    TEMPLATE_IN  bool  CLASS::is_end_of_file() 
    {
        ASSERT_CONSISTENCY();
        // if the end of file pointer is not set, then there is no EOF inside the buffer
        if( _end_of_file_p == 0x0 )        { return false; }

        // if the 'current' pointer points to the place of EOF then, that's what is to say about it
        if( _current_p == _end_of_file_p ) { return true; }

        return false;
    }

    TEMPLATE_IN  bool  CLASS::is_begin_of_file() 
    {
        ASSERT_CONSISTENCY();
        // if buffer does not start at 'begin of file', then there is no way that we're there
        if( _character_index_at_front != 0 ) { return false; }

        // if we're at the beginning of the buffer, then this is also the beginning of the file
        if( _current_p == _buffer.front() ) { return true; }

        return false;
    }

    TEMPLATE_IN  bool  CLASS::is_begin_of_buffer()
    {
        ASSERT_CONSISTENCY();
        return _current_p == _buffer.front();
    }

    TEMPLATE_IN  bool  CLASS::is_end_of_buffer()
    {
        ASSERT_CONSISTENCY();
        return _current_p == _buffer.back();
    }

    TEMPLATE_IN  void CLASS::set_subsequent_character(const int Value) { ASSERT_CONSISTENCY(); *(_current_p + 1) = Value; }
    TEMPLATE_IN  void CLASS::set_current_p(character_type* Adr)        { _current_p = Adr; ASSERT_CONSISTENCY(); }

    TEMPLATE_IN  typename CLASS::character_type    
        CLASS::get_subsequent_character() 
        { ASSERT_CONSISTENCY(); return *(_current_p + 1); }

    TEMPLATE_IN  typename CLASS::character_type    
        CLASS::get_current_character() 
        { ASSERT_CONSISTENCY(); return *_current_p; }

    TEMPLATE_IN void CLASS::mark_lexeme_start() 
    { 
        _lexeme_start_p = _current_p + 1;  // pointing to the next character to be read   
        ASSERT_CONSISTENCY();
    }


    TEMPLATE_IN void CLASS::__end_of_file_set(character_type* EOF_p)
    {
        _end_of_file_p  = EOF_p; 
        *_end_of_file_p = CLASS::BLC; 
        ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN  void CLASS::__end_of_file_unset()
    {
        _end_of_file_p   = 0x0; 
        ASSERT_CONSISTENCY();
    }


    TEMPLATE_IN  typename CLASS::character_type* CLASS::get_lexeme_start_p()
    {
        ASSERT_CONSISTENCY();
        return _lexeme_start_p;
    }

    TEMPLATE_IN  typename CLASS::memory_position CLASS::tell_adr()
    {
        ASSERT_CONSISTENCY();
#           ifndef QUEX_OPTION_ACTIVATE_ASSERTS
        return memory_position(_current_p, _character_index_at_front);
#           else
        return memory_position(_current_p);
#           endif
    }

    TEMPLATE_IN  void CLASS::seek_adr(const memory_position Adr)
    {
#           ifndef QUEX_OPTION_ACTIVATE_ASSERTS
        // Check wether the memory_position is relative to the current start position 
        // of the stream. That means, that the tell_adr() command was called on the
        // same buffer setting or the positions have been adapted using the += operator.
        const long begin_pos = _character_index_at_front; 
        __quex_assert(Adr.buffer_start_position == _character_index_at_front);
        _current_p = Adr.address;
#           else
        _current_p = Adr;
#           endif
        ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN  void CLASS::seek_offset(const int Offset)
    {
        _current_p += Offset;

        ASSERT_CONSISTENCY();
    }

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

    TEMPLATE_IN  void CLASS::move_backward(const size_t Distance)
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

#undef TEMPLATE_IN
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
