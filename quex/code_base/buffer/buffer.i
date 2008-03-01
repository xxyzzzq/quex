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
               character_type Value_BOFC /* = DEFAULT_BUFFER_BEGIN_OF_FILE_CODE */,
               character_type Value_EOFC /* = DEFAULT_BUFFER_END_OF_FILE_CODE */,
               character_type Value_BLC  /* = DEFAULT_BUFFER_LIMIT_CODE */)
        : BASE_CLASS(BufferSz, BackupSectionSz, 
                     Value_BOFC, Value_EOFC, Value_BLC),
        _input(input_strategy)
    {
        __constructor_core();
    }
                  

    TEMPLATE inline
        CLASS::basic_buffer(input_handle_type* input_handle, 
                            size_t BufferSz/* = 65536 */, size_t BackupSectionSz/* = 64 */,
                            character_type Value_BOFC /* = DEFAULT_BUFFER_BEGIN_OF_FILE_CODE */,
                            character_type Value_EOFC /* = DEFAULT_BUFFER_END_OF_FILE_CODE */,
                            character_type Value_BLC  /* = DEFAULT_BUFFER_LIMIT_CODE */)   
        : BASE_CLASS(BufferSz, BackupSectionSz, 
                     Value_BOFC, Value_EOFC, Value_BLC),
        _input(InputStrategy(input_handle))
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
            assert(fill_start_adr     >= this->content_begin());
            assert(fill_start_adr + N <= this->content_end());
            //______________________________________________________________________________
            const int ReadN = _input.read(fill_start_adr, N); 

            return ReadN;
        }


    template<class InputStrategy, class OverflowPolicy> inline int  
        basic_buffer<InputStrategy, OverflowPolicy>::load_forward() {
            // RETURNS: Distance that was loaded forward in the stream.
            //          -1 in case that forward loading was not possible (end of file)
            this->EMPTY_or_show_buffer_load("LOAD FORWARD(entry)");

            // This function assumes that the _current_p has reached either
            // the buffer's border, or the _end_of_file_p.
            if( this->_end_of_file_p ) {
                if( this->_current_p != this->_end_of_file_p ) {
                    throw std::range_error("Inaddmissible 'EndOfFile' character code appeared in input stream.\n" 
                                           "(Check character encoding)");  
                }
            }
            else if( this->_current_p != this->_buffer + this->BUFFER_SIZE - 1) {
                throw std::range_error("Inaddmissible 'BufferLimit' character code appeared in input stream.\n" 
                                       "(Check character encoding)");  
            }
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);
            //
            // If the lexeme start pointer is at the beginning of the buffer,
            // then no new content can be loaded without a special strategy.
            // At this point '=0' is permitted, but downwards we call a virtual
            // function that handles this case, derive from this class to 
            // implement your personal strategy to handle this. 
            const int LexemeStartOffSet = this->_lexeme_start_p - this->content_begin();

            if( this->_end_of_file_p ) return -1; 
            // buffer:
            //             fallback_n
            //                :
            // |11111111111111:22222222222222222222222222222222222222|
            //   copy of      :   new loaded content of buffer
            //   end of old   
            //   buffer      
            this->_current_fallback_n = this->FALLBACK_N;

            // (*) calculate the fallback area:
            //     -- the lexeme start pointer has to be inside the buffer 
            //        content_size() - LexemeStartOffSet  - 1 >= border
            if( this->content_size() - LexemeStartOffSet > this->_current_fallback_n ) {
                this->_current_fallback_n = this->content_size() - LexemeStartOffSet;
                if( this->_current_fallback_n == this->content_size() ) {
                    // if the lexeme covers the whole buffer, than the _current_fallback_n would reach
                    // the end of the buffer. this is a case for a call to a virtual event
                    // handler: 
                    if( OverflowPolicy::forward(this) == false ) return -1;
                }
            }
            //     -- there cannot be more fallback than what was read
            size_t putback_n = this->_current_p - this->content_begin();
            if( putback_n > this->_current_fallback_n ) putback_n = this->_current_fallback_n;

            // (*) copy fallback content
            std::memmove(this->content_begin() + this->_current_fallback_n - putback_n, 
                         this->content_end() - putback_n, putback_n);

            // (*) load new content starting from beyond the fallback border
            const stream_position CurrentPos = _input.tell();
            const stream_position EndPosOfBuffer(this->_start_pos_of_buffer + 
                                                 (stream_offset)(this->content_size()));
            if( ! (EndPosOfBuffer == CurrentPos) ) _input.seek(EndPosOfBuffer);

            const size_t LoadN   = this->content_size() - this->_current_fallback_n;
            const size_t LoadedN = __load_core(this->content_begin() + this->_current_fallback_n, LoadN);

            // -- end of file / end of buffer:
            if( LoadedN != LoadN ) this->__set_end_of_file(this->content_begin() + this->_current_fallback_n + LoadedN);
            else                   this->__unset_end_of_file();

            // -- begin of file / begin of buffer
            //    any 'load forward' undoes a 'begin of file touched', since now we can
            //    try to read again backwards. reading of zero bytes is impossible, since
            //    FALLBACK_N has to be < content_size().
            this->__unset_begin_of_file();

            // (*) adapt pointers
            // next char to be read: '_current_p + 1'
            this->_current_p = this->content_begin() + this->_current_fallback_n - 1;   
            // LoadN = number of elements deleted
            //       => independent on number of elements that were actually read !!
            this->_lexeme_start_p      = this->content_begin() + LexemeStartOffSet - LoadN; 
            this->_start_pos_of_buffer = _input.tell() - (stream_position)(LoadedN + this->_current_fallback_n);
            // NOTE: Return value used for adaptions of memory addresses. The same rule as for
            //       _lexeme_start_p holds for those addresses.

            this->EMPTY_or_show_buffer_load("LOAD FORWARD(exit)");
            this->EMPTY_or_assert_consistency(/* allow terminating zero = */false);
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
            // the lower border of the buffer. 
            if( this->_current_p != this->content_begin() - 2 ) 
                throw std::range_error("Inaddmissible character code appeared in input stream.\n" 
                                       "(Check character encoding)");  

            const int LexemeStartOffSet = this->_lexeme_start_p - this->content_begin();
            //_______________________________________________________________________________
            if( *(this->buffer_begin()) == basic_buffer::BOFC ) return -1; // we cannot go further back

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
#ifndef NDEBUG
            const size_t LoadedN = __load_core(this->content_begin(), backward_distance);
            // -- If file content < buffer size, then the start position of the stream to which
            //    the buffer refers is always 0 and no backward loading will ever happen.
            // -- If the file content >= buffer size, then backward loading must always fill
            //    the buffer. 
            assert(LoadedN == (size_t)backward_distance);
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

#ifdef __QUEX_OPTION_UNIT_TEST
    TEMPLATE inline void 
        CLASS::show_brief_content() {
            std::cout << "start-pos:  " << this->_start_pos_of_buffer << std::endl;
            const stream_position  Pos = this->_input.tell();
            std::cout << "stream-pos: " << Pos << std::endl;
            std::cout << "EOF = " << bool(this->_end_of_file_p);
            std::cout << ", BOF = " << bool(*(this->buffer_begin()) == basic_buffer::BOFC) << std::endl;
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
