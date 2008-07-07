// -*- C++ -*-   vim: set syntax=cpp:
inline void    
CLASS::move_forward(const size_t Distance)
{
    this->__buffer->move_forward(Distance);
}

inline void    
CLASS::move_backward(const size_t Distance)
{
    this->__buffer->move_backward(Distance);
}

inline void
CLASS::_reset()
{
    // NOTE: We do not create a new buffer here, since we assume that it has been created
    QUEX_CORE_ANALYSER_STRUCT_init(this, 0, /* use same current buffer */0x0, 
                                   mode_db[__QUEX_SETTING_INITIAL_LEXER_MODE_ID]->analyser_function);

#   if   defined(QUEX_OPTION_LINE_NUMBER_COUNTING)          \
       | defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)        \
       | defined(__QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT)
    counter.init();
#   endif

    // empty the token queue
#   ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE
    this->_token_queue->reset();
#   endif

    set_mode_brutally(__QUEX_SETTING_INITIAL_LEXER_MODE_ID);

    __previous_mode_p = __current_mode_p;  // required for detection of mode changes inside
    //                                     // pattern actions
    __continue_analysis_after_adapting_mode_function_p_f = false;

    // Reset the buffer
    this->__buffer->_reset();
}

