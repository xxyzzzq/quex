
    TEMPLATE_IN  bool  CLASS::is_end_of_file() 
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY();
        // if the end of file pointer is not set, then there is no EOF inside the buffer
        if( _end_of_file_p == 0x0 )        { return false; }

        // if the 'current' pointer points to the place of EOF then, that's what is to say about it
        if( _current_p == _end_of_file_p ) { return true; }

        return false;
    }

    TEMPLATE_IN  bool  CLASS::is_begin_of_file() 
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY();
        // if buffer does not start at 'begin of file', then there is no way that we're there
        if( _character_index_at_front != 0 ) { return false; }

        // if we're at the beginning of the buffer, then this is also the beginning of the file
        if( _current_p == _buffer.front() ) { return true; }

        return false;
    }

    TEMPLATE_IN  bool  CLASS::is_begin_of_buffer()
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY();
        return _current_p == _buffer.front();
    }

    TEMPLATE_IN  bool  CLASS::is_end_of_buffer()
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY();
        return _current_p == _buffer.back();
    }

    TEMPLATE_IN  void CLASS::set_current_character(const CharacterCarrierType Value) 
    { QUEX_BUFFER_ASSERT_CONSISTENCY(); *(_current_p) = Value; }
    TEMPLATE_IN  void CLASS::set_current_p(character_type* Adr)     
    { _current_p = Adr; QUEX_BUFFER_ASSERT_CONSISTENCY(); }

    TEMPLATE_IN  typename CLASS::character_type    
        CLASS::get_previous_character() 
        { QUEX_BUFFER_ASSERT_CONSISTENCY(); return *(_current_p - 1); }

    TEMPLATE_IN  typename CLASS::character_type    
        CLASS::get_current_character() 
        { QUEX_BUFFER_ASSERT_CONSISTENCY(); return *_current_p; }

    TEMPLATE_IN void CLASS::mark_lexeme_start() 
    { 
        _lexeme_start_p = _current_p;  // pointing to the next character to be read   
        QUEX_BUFFER_ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN  typename CLASS::character_type* 
    CLASS::get_lexeme_start_p()
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY();
        return _lexeme_start_p;
    }

    TEMPLATE_IN  typename CLASS::memory_position CLASS::tell_adr()
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY();
#       ifdef QUEX_OPTION_ACTIVATE_ASSERTS
        return memory_position_mimiker<CharacterCarrierType>(_current_p, _character_index_at_front);
#       else
        return memory_position(_current_p);
#       endif
    }

    TEMPLATE_IN  void CLASS::seek_adr(const memory_position Adr)
    {
#       ifdef QUEX_OPTION_ACTIVATE_ASSERTS
        // Check wether the memory_position is relative to the current start position 
        // of the stream. That means, that the tell_adr() command was called on the
        // same buffer setting or the positions have been adapted using the += operator.
        __quex_assert(Adr.buffer_start_position == _character_index_at_front);
        _current_p = Adr.address;
#       else
        _current_p = Adr;
#       endif
        QUEX_BUFFER_ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN  void CLASS::seek_offset(const int Offset)
    {
        _current_p += Offset;

        QUEX_BUFFER_ASSERT_CONSISTENCY();
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
            QUEX_BUFFER_ASSERT_CONSISTENCY();
            if( _end_of_file_p != 0x0 ) {
                if( _current_p + remaining_distance_to_target >= _end_of_file_p ) {
                    _current_p      = _end_of_file_p;
                    _lexeme_start_p = _current_p;
                    QUEX_BUFFER_ASSERT_CONSISTENCY();
                    return;
                } 
            } else {
                if( _current_p + remaining_distance_to_target < _buffer.back() ) {
                    _current_p      += remaining_distance_to_target;
                    _lexeme_start_p  = _current_p + 1;
                    QUEX_BUFFER_ASSERT_CONSISTENCY();
                    return;
                }
            }

            // move current_p to end of the buffer, thus decrease the remaining distance
            remaining_distance_to_target -= (_buffer.back() - _current_p);
            _current_p      = _buffer.back();
            _lexeme_start_p = _buffer.back();

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
            if( _current_p - remaining_distance_to_target <= content_front() ) {
                if( *(_buffer.front()) == CLASS::BLC ) {
                    _current_p      = content_front();
                    _lexeme_start_p = content_front() + 1; 
                    QUEX_BUFFER_ASSERT_CONSISTENCY();
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

