// : -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2007 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_

namespace quex {
#   define TEMPLATE   template<class InputStrategy, class OverflowPolicy>
#   define CLASS      basic_buffer<InputStrategy, OverflowPolicy>   
#   define BASE_CLASS buffer_core<typename InputStrategy::provided_character_type>

    TEMPLATE inline
        CLASS::basic_buffer(InputStrategy& input_strategy, 
               size_t BufferSz /* = 65536 */, size_t BackupSectionSz /* = 64 */,
               character_type Value_BLC  /* = DEFAULT_BUFFER_LIMIT_CODE */)
        : BASE_CLASS(BufferSz, BackupSectionSz, Value_BLC), _input(input_strategy)
    {
        __constructor_core();
    }
                  

    TEMPLATE inline
        CLASS::basic_buffer(input_handle_type* input_handle, 
                            size_t BufferSz/* = 65536 */, size_t BackupSectionSz/* = 64 */,
                            character_type Value_BLC  /* = DEFAULT_BUFFER_LIMIT_CODE */)   
        : BASE_CLASS(BufferSz, BackupSectionSz, Value_BLC), _input(InputStrategy(input_handle))
    {
        __constructor_core();
    }

    TEMPLATE inline void  
        CLASS::__constructor_core()
    {
        // -- load initial content starting from position zero
        const size_t LoadedN = __load_core(BASE_CLASS::content_begin(), BASE_CLASS::content_size());

        this->_start_pos_of_buffer = _input.tell() - (stream_position)(LoadedN);

        // -- the fallback border (this->_current_fallback_n is required for 'show' functions)
        this->_current_fallback_n  = this->FALLBACK_N;

        // -- end of file / end of buffer:
        if( LoadedN != this->content_size() ) 
            this->__set_end_of_file(this->content_begin() + LoadedN); // end of file
        else
            this->__unset_end_of_file();                              // buffer limit
        
        // -- begin of buffer?
        if( this->_start_pos_of_buffer == (stream_position)(0) ) 
            this->__set_begin_of_file();   // begin of file                
        else
            this->__unset_begin_of_file(); // buffer limit

        this->EMPTY_or_assert_consistency(/* allow terminating zero = */ false);
    }

    TEMPLATE inline int  
        CLASS::__load_core(character_type* fill_start_adr, const int N) {
            // -- Reads N bytes into buffer starting at 'fill_start_adr'. If less then
            //    N bytes could be read, the end of file flag is raised.
            //  
            __quex_assert(fill_start_adr     >= this->content_begin());
            __quex_assert(fill_start_adr + N <= this->content_end());
            //______________________________________________________________________________
            const int ReadN = _input.read_characters(fill_start_adr, N); 

            return ReadN;
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
            //
            // RETURNS: '>= 0'   number of characters that were loaded forward in the stream.
            //          '-1'     if forward loading was not possible (end of file)
            this->EMPTY_or_show_buffer_load("LOAD FORWARD(entry)");

            // (*) Check for the three possibilities mentioned above
            if     ( this->_current_p == this->buffer_begin() ) { return 0; }
            else if( this->_current_p == this->_end_of_file_p ) { return -1; }
            else if( this->_current_p != this->buffer_end() ) {
                throw std::range_error("Inaddmissible 'BufferLimit' character code appeared in input stream.\n" 
                                       "(Check character encoding)");  
            }
            //
            // NOTE: From here on, the current pointer points to the END OF THE BUFFER!
            // 
            // (*) Double check on consistency
            //     -- 'load_forward()' should only be called, if the '_current_p' reached a border.
            //        Since we know from above, that we did not reach end of file, it can be assumed
            //        that the _end_of_file_p == 0x0 (buffer does not contain EOF).
            __quex_assert(this->_end_of_file_p == 0x0);
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);

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

            // (2) Load new content
            //
            //     ** The current end position of the buffer needs to be STORED in '_end_pos_of_buffer' **
            //     ** It cannot be computed by _start_pos_of_buffer + buffer_size, since some character **
            //     ** encodings need varying number of bytes for different characters (e.g. UTF-8).     **
            //
            if( this->tell() != this->_end_pos_of_buffer ) _input.seek(this->_end_pos_of_buffer);

            const size_t    LoadN       = this->content_size() - FallBackN;
            // (*) If more characters need to be loaded than the buffer can hold,
            //     then this is a critical overflow. Example: If lexeme extends over 
            //     the whole buffer (==> MinFallbackN >= content_size).
            if( LoadN == 0 ) { if( OverflowPolicy::forward(this) == false ) return -1; }

            character_type* new_content = this->content_begin() + FallBackN;
            const size_t    LoadedN     = __load_core(new_content, LoadN);

            //     If end of file has been reached, then the 'end of file' pointer needs to be set
            if( LoadedN != LoadN ) this->__set_end_of_file(this->content_begin() + FallBackN + LoadedN);
            else                   this->__unset_end_of_file();

            //    Since 'LoadN != 0' it is safe to say that some characters have been loaded and we
            //    are no longer at the beginning of the file.
            this->__unset_begin_of_file();

            // (3) Pointer adaption
            //     Next char to be read: '_current_p + 1'
            this->_current_p         = this->content_begin() + this->_current_fallback_n - 1;   
            //     MinFallbackN = distance from '_lexeme_start_p' to '_current_p'
            this->_lexeme_start_p    = this->_current_p - MinFallbackN; 
            this->_end_pos_of_buffer = _input.tell();

            this->EMPTY_or_show_buffer_load("LOAD FORWARD(exit)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);

            // NOTE: Return value used for adaptions of memory addresses. The same rule as for
            //       _lexeme_start_p holds for those addresses.
            return LoadN;
        }

    TEMPLATE inline int  
        CLASS::load_backward() {
            // RETURNS: Distance that was loaded backwards.
            //          -1 in case of backward loading is not possible (begin of file)
            //     
            // PURPOSE: 
            //     
            // Going backwards, because a call to get_backward() hit the front
            // of the buffer. Usually, there are the 'FALLBACK_N' buffer bytes that
            // allows a certain distance backwards. If still the begin of the
            // buffer is reached, then this is an indication that something is
            // 'off-the-norm'. Lexical analysis is not supposed to go longtimes
            // backwards. For such cases we step a long stretch backwards: A
            // THIRD of the buffer's size! 
            //
            // A meaningful fallback_n would be 10 Bytes. If the buffer's size
            // is for example 512 kB then the backwards_distance of A THIRD means 170
            // kB. This leaves a  safety region which is about 17.476 times
            // greater than normal (10 Bytes). After all, lexical analysis means
            // to go mainly forward and not backwards.
            //
            this->EMPTY_or_show_buffer_load("LOAD BACKWARD(entry)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);

            // This function should only be called when the iterator has reached 
            // the lower border of the buffer. Detection, though happens on the Buffer Limit Code.
            // A special use case is where the current pointer stands on 'end of file' which
            // is also labeled as 'BLC'. If at this momement a 'get_backward()' is applied
            // this reports also a 'BLC' and we are here in this part of the code.
            // => Thus, if the current_p points to _end_of_file_p then we simply know that there
            //    is nothing to load and return.
            if( this->_current_p != this->buffer_begin() - 1 ) { 
                if(    this->_current_p + 1 == this->_end_of_file_p 
                    || this->_current_p + 1 == this->buffer_end() ) return /* backward distance = */0; 
                throw std::range_error("Buffer reload backwards where 'current' does not point to buffer -1.\n" 
                                       "(Check character encoding)");  
            }

            const int LexemeStartOffSet = this->_lexeme_start_p - this->content_begin();
            //_______________________________________________________________________________
            if( this->_start_pos_of_buffer == 0 ) return -1; // we cannot go further back

            // (*) compute the distance to go backwards
            int backward_distance = (int)(this->content_size() / 3);   // go back a third of the buffer 
            //
            if( this->_start_pos_of_buffer < (stream_position)backward_distance ) 
                backward_distance = (int)(this->_start_pos_of_buffer); 

            // -- _lexeme_start_p shall never be beyond the content limit
            if( (size_t)(LexemeStartOffSet + backward_distance) > this->content_size() ) {
                // later on: 
                //      _lexeme_start_p (new) = _lexeme_start_p (old) + backward_distance
                // thus extreme case:
                //      content_end() - 1 = _lexeme_start_p (old) + backward_distance
                // with:
                //      LexemeStartOffSet = _lexeme_start_p - content_begin()
                backward_distance =this->content_size() - LexemeStartOffSet - 1;
            }
            if( backward_distance <= 0 ) 
                if( OverflowPolicy::backward(this) == false ) return -1;


            // (*) copy content that is already there to its new position.
            //     (copying is much faster then loading new content from file)
            std::memmove(this->content_begin() + backward_distance,
                         this->content_begin(),this->content_size() - backward_distance);

            // (*) load content
            _input.seek(this->_start_pos_of_buffer - (stream_offset)(backward_distance));
#ifdef QUEX_OPTION_ACTIVATE_ASSERTS
            const size_t LoadedN = __load_core(this->content_begin(), backward_distance);
            // -- If file content < buffer size, then the start position of the stream to which
            //    the buffer refers is always 0 and no backward loading will ever happen.
            // -- If the file content >= buffer size, then backward loading must always fill
            //    the buffer. 
            __quex_assert(LoadedN == (size_t)backward_distance);
#else
            __load_core(this->content_begin(), backward_distance);  // avoid unused LoadedN
#endif
            // -- end of file / end of buffer:
            if( this->_end_of_file_p ) {
                character_type*   NewEndOfFileP = this->_end_of_file_p + backward_distance;
                if( NewEndOfFileP <this->content_end() ) this->__set_end_of_file(NewEndOfFileP);
                else                                     this->__unset_end_of_file();
            }
            if( (stream_position)backward_distance == this->_start_pos_of_buffer ) this->__set_begin_of_file();
            else                                                                   this->__unset_begin_of_file();

            // (*) set the read pointer
            this->_current_p            = this->_current_p + backward_distance + 1; 
            this->_lexeme_start_p       = this->_lexeme_start_p + backward_distance;
            this->_start_pos_of_buffer -= backward_distance;  

            //________________________________________________________________________________
            // -- any 'load backward' undoes a 'end of file touched', since now we can
            //    try to read again backwards.
            this->EMPTY_or_show_buffer_load("LOAD BACKWARD(exit)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);
            return backward_distance;
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

            // if buffer does not start at 'begin of file', then there is no way that we're at BOF
            if( this->_start_pos_of_buffer != 0 )   { return false; }

            // if we're at the beginning of the buffer, then this is also the beginning of the file
            if( this->_current_p == this->buffer_begin() - 1 ) { return true; }

            // double check: the 'current' pointer shall never be put below the buffer start
            __quex_assert(this->_current_p < this->buffer_begin() );
            if( this->_current_p < this->buffer_begin() - 1 ) { return true; } // strange urgency ...
            return false;
        }


#ifdef __QUEX_OPTION_UNIT_TEST
    TEMPLATE inline void 
        CLASS::show_brief_content() {
            std::cout << "start-pos:  " << this->_start_pos_of_buffer << std::endl;
            const stream_position  Pos = this->_input.tell();
            std::cout << "stream-pos: " << Pos << std::endl;
            std::cout << "EOF = "       << bool(this->_end_of_file_p);
            std::cout << ", BOF = "     << bool(_start_pos_of_buffer == 0) << std::endl;
            std::cout << "current_p (offset)    = " << this->_current_p - this->content_begin() << std::endl;
            std::cout << "lexeme start (offset) = " << this->_lexeme_start_p - this->content_begin() << std::endl;
        }
    TEMPLATE inline void 
        CLASS::x_show_content() {
            this->show_content();
            show_brief_content();
        }
#endif

#ifndef __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS
    TEMPLATE inline void CLASS::EMPTY_or_show_buffer_load(const char* InfoStr) { }
#else
    TEMPLATE inline void 
        CLASS::EMPTY_or_show_buffer_load(const char* InfoStr)
        {
            std::cout << InfoStr << "\n";
            this->show_content();
        }
#endif

#undef TEMPLATE
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_I_
