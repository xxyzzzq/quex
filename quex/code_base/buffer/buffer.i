// : -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2007 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_

namespace quex {
#   define TEMPLATE   template<class CharacterCarrierType>
#   define CLASS      buffer<CharacterCarrierType>   

    TEMPLATE inline
        CLASS::basic_buffer(input_strategy<CharacterCarrierType>* _input_strategy, 
               size_t BufferSz /* = 65536 */, size_t BackupSectionSz /* = 64 */,
               character_type Value_BLC  /* = DEFAULT_BUFFER_LIMIT_CODE */)
        : BASE_CLASS(BufferSz, BackupSectionSz, Value_BLC), _input(_input_strategy)
    {
        __constructor_core();
    }
                  

    TEMPLATE inline void  
        CLASS::__constructor_core(CharacterCarrierType* buffer_memory, const size_t BufferSize)
    {
        __quex_assert(BUFFER_SIZE > 2); 
        __quex_assert(FALLBACK_N < BUFFER_SIZE - 2);  // '-2' because of the border chars.
        //___________________________________________________________________________
        //
        // NOTE: The borders are filled with buffer limit codes, end of file or
        //       begin of file codes. Thus the buffer's volume is two elements greater
        //       then the buffer's content.
        //
        if( buffer_memory == 0x0 ) _buffer.begin = new character_type[BufferSize];      
        else                       _buffer.begin = buffer_memory;
        _buffer.end = _buffer.begin + BufferSize;

        // _buffer[0]             = lower buffer limit code character
        // _buffer[1]             = first char of content
        // _buffer[BUFFER_SIZE-2] = last char of content
        // _buffer[BUFFER_SIZE-1] = upper buffer limit code character
        _buffer.begin[0]            = CLASS::BLC; // set buffer limit code
        _buffer.begin[BufferSize-1] = CLASS::BLC; // set buffer limit code

        // -- current = 1 before content, 
        //    because we always read '_current_p + 1' as next char.
        _current_p      = _buffer.begin;     
        // -- initial lexeme start, of course, at the start
        _lexeme_start_p = _buffer.begin + 1;

        // -- for a later 'map_to_stream_position(character_index), the strategy might
        //    have some plans.
        _input.register_current_position_for_character_index_equal_zero();

        // -- load initial content starting from position zero
        const size_t LoadedN = _input.read_characters(content_begin(), content_size());
        __quex_assert(LoadedN <= content_size());

        this->_character_index_at_begin = 0;

        // -- the fallback border (this->_current_fallback_n is required for 'show' functions)
        this->_current_fallback_n  = this->FALLBACK_N;

        // -- end of file / end of buffer:
        if( LoadedN != this->content_size() ) 
            this->__end_of_file_set(content_begin() + LoadedN); // end of file
        else
            this->__end_of_file_unset();                        // buffer limit

        ASSERT_CONSISTENCY();
    }

    TEMPLATE inline
        CLASS::~buffer_core() {
            delete [] _buffer;
        }


    TEMPLATE inline int  
        CLASS::load_forward() {
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
            this->EMPTY_or_show_buffer_load("LOAD FORWARD(entry)");

            // (*) Check for the three possibilities mentioned above
            if     ( this->_current_p == this->buffer_begin() ) { return 0; }       // (1)
            else if( this->_current_p == this->_end_of_file_p ) { return -1; }      // (2)
            else if( this->_current_p != this->buffer_end() ) {                     
                throw std::range_error("Inaddmissible 'BufferLimit' character code appeared in input stream.\n" 
                                       "(Check character encoding)");  
            }
            //                                                                      // (3)

            //
            // HERE: current_p == END OF THE BUFFER!
            // 

            // (*) Double check on consistency
            //     -- 'load_forward()' should only be called, if the '_current_p' reached a border.
            //        Since we know from above, that we did not reach end of file, it can be assumed
            //        that the _end_of_file_p == 0x0 (buffer does not contain EOF).
            __quex_assert(this->_end_of_file_p == 0x0);
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);

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
            __quex_assert(this->_current_p >= this->_lexeme_start_p);
            const int MinFallbackN = this->_current_p - this->_lexeme_start_p;

            // (*) Fallback region = max(default size, necessary size)
            const int FallBackN = this->FALLBACK_N > MinFallbackN ? this->FALLBACK_N : MinFallbackN;

            // (*) Copy fallback region
            //     If there is no 'overlap' from source and drain than the faster memcpy() can 
            //     used instead of memmove().
            character_type* source = this->content_end() - this->_current_fallback_n;
            character_type* drain  = this->content_begin();
            if( drain + FallBackN >= source  ) {
                std::memmove(drain, source, FallBackN * sizeof(character_type));
            } else { 
                std::memcpy(drain, source, FallBackN * sizeof(character_type));
            }
            this->_current_fallback_n = FallBackN;

            //___________________________________________________________________________________
            // (2) Load new content
            //
            // The input_strategy emulates a stream of characters of constant width, independtly 
            // of the character coding that is used. Thus, it is safe to compute the position at the
            // end of the buffer by simple addition of 'content size' to '_character_index_at_begin'.
            //
            const int CharacterIndexAtEnd = this->_character_index_at_begin + (BUFFER_SIZE - 2);
            if( _input.tell_character_index() != CharacterIndexAtEnd  ) { 
                _input.seek_character_index(CharacterIndexAtEnd);
            }

            const size_t    LoadN       = this->content_size() - FallBackN;
            // (*) If more characters need to be loaded than the buffer can hold,
            //     then this is a critical overflow. Example: If lexeme extends over 
            //     the whole buffer (==> MinFallbackN >= content_size).
            if( LoadN == 0 ) { if( OverflowPolicy::forward(this) == false ) return -1; }

            character_type* new_content = this->content_begin() + FallBackN;
            const size_t    LoadedN     = _input.read_characters(new_content, LoadN);

            //     If end of file has been reached, then the 'end of file' pointer needs to be set
            if( LoadedN != LoadN ) this->__end_of_file_set(this->content_begin() + FallBackN + LoadedN);
            else                   this->__end_of_file_unset();

            this->_character_index_at_begin += LoadN - FallBackN;
            this->_character_index_at_end   += LoadedN - FallBackN;

            //___________________________________________________________________________________
            // (3) Pointer adaption
            //     Next char to be read: '_current_p + 1'
            this->_current_p         = this->content_begin() + FallBackN - 1;   
            //     MinFallbackN = distance from '_lexeme_start_p' to '_current_p'
            this->_lexeme_start_p    = this->_current_p - MinFallbackN; 

            this->EMPTY_or_show_buffer_load("LOAD FORWARD(exit)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);

            // NOTE: Return value used for adaptions of memory addresses. The same rule as for
            //       _lexeme_start_p holds for those addresses.
            return LoadN;
        }

    TEMPLATE inline int  
        CLASS::load_backward() {
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
            this->EMPTY_or_show_buffer_load("LOAD BACKWARD(entry)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);

            // (*) Check for the three possibilities mentioned above
            if     ( this->_current_p == this->buffer_end() )   { return 0; }   // (1)
            else if( this->_current_p == this->_end_of_file_p ) { return 0; }   // (1)
            else if( this->current_p != this->buffer_begin()) {
                throw std::range_error("Inaddmissible 'BufferLimit' character code appeared in input stream.\n" 
                                       "(Check character encoding)");  
            }
            else if( this->_begin_of_file_f ) { return -1; }                    // (2)
            //                                                                  // (3)
            // HERE: current_p == BEGIN OF THE BUFFER!
            //

            //_______________________________________________________________________________
            // (1) Compute distance to go backwards
            //
            //     We need to make sure, that the lexeme start pointer remains inside the
            //     buffer, so that we do not loose the reference. From current_p == buffer begin
            //     it is safe to say that _lexeme_start_p > _current_p (the lexeme starts
            //     on a letter not the buffer limit).
            __quex_assert(this->_lexeme_start_p > _current_p);
            const int IntendedBackwardDistance = (int)(this->content_size() / 3);   

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
            if( this->_lexeme_start_p == this->content_end() ) {
                if( OverflowPolicy::backward(this) == false ) return -1;
            }
            const int MaxBackwardDistance =   this->content_size() 
                                            - (int)(this->_lexeme_start_p - this->_current_p);
            const int BackwardDistance = IntendedBackwardDistance > MaxBackwardDistance ? 
                                             MaxBackwardDistance : IntendedBackwardDistance;

            //_______________________________________________________________________________
            // (2) Compute the stream position of the 'start to read' 
            //
            // It is not safe to assume that the character size is fixed. Thus it is up to
            // the input strategy to determine the input position that belongs to a character
            // position.
            int start_character_index =   this->_character_index_at_begin
                                        - BackwardDistance;
            if( start_character_index < 0 ) start_character_index = 0;

            const stream_position    start_pos = _input.map_to_stream_position(start_character_index);

            // (*) copy content that is already there to its new position.
            //     (copying is much faster then loading new content from file)
            std::memmove(this->content_begin() + BackwardDistance,
                         this->content_begin(),this->content_size() - BackwardDistance);

            //_______________________________________________________________________________
            // (3) Load content
            //
            _input.seek(start_pos);
#           ifdef QUEX_OPTION_ACTIVATE_ASSERTS
            const size_t LoadedN = // avoid unused variable in case '__quex_assert()' is deactivated
#           endif
            _input.read_characters(this->content_begin(), BackwardDistance);
            // -- If file content < buffer size, then the start position of the stream to which
            //    the buffer refers is always 0 and no backward loading will ever happen.
            // -- If the file content >= buffer size, then backward loading must always fill
            //    the buffer. 
            __quex_assert(LoadedN == (size_t)BackwardDistance);

            _input.read_characters(this->content_begin(), BackwardDistance);

            // -- end of file / end of buffer:
            if( this->_end_of_file_p ) {
                character_type*   NewEndOfFileP = this->_end_of_file_p + BackwardDistance;
                if( NewEndOfFileP < this->content_end() ) this->__end_of_file_set(NewEndOfFileP);
                else                                      this->__end_of_file_unset();
            }
            this->_character_index_at_begin -= BackwardDistance;

            //________________________________________________________________________________
            // (4) Adapt pointers
            //
            this->_current_p            = this->_current_p + BackwardDistance + 1; 
            this->_lexeme_start_p       = this->_lexeme_start_p + BackwardDistance;
            this->_start_pos_of_buffer -= BackwardDistance;  

            this->EMPTY_or_show_buffer_load("LOAD BACKWARD(exit)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);
            return BackwardDistance;
        }

    TEMPLATE inline const bool  
        CLASS::is_end_of_file() {
            __quex_assert(this->_current_p <= this->buffer_end() );
            __quex_assert(this->_current_p >= this->buffer_begin() );

            // if the end of file pointer is not set, then there is no EOF inside the buffer
            if( this->_end_of_file_p == 0x0 )              { return false; }
            
            // if the 'current' pointer points to the place of EOF then, that's what is to say about it
            if( this->_current_p == this->_end_of_file_p ) { return true; }

            // double check: the 'current' pointer shall never be put beyond the end of file pointer
            __quex_assert(this->_current_p < this->_end_of_file_p);
            if( this->_current_p < this->buffer_begin() )  { return true; } // strange urgency ...
            return false;
        }

    TEMPLATE inline const bool  
        CLASS::is_begin_of_file() {
            __quex_assert(this->_current_p <= this->buffer_end() );
            __quex_assert(this->_current_p >= this->buffer_begin() );

            // if buffer does not start at 'begin of file', then there is no way that we're there
            if( this->_character_index_at_begin != 0 ) { return false; }

            // if we're at the beginning of the buffer, then this is also the beginning of the file
            if( this->_current_p == this->buffer_begin() ) { return true; }

            return false;
        }



#undef TEMPLATE
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
