// -*- C++ -*- vim:set syntax=cpp:
template <class InputHandle> inline void    
CLASS::include_stack_push(InputHandle*      new_input_handle_p, 
                          const quex_mode&  mode, 
                          const char*       IConvInputCodingName /* = 0x0 */)
{
    // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
    __include_stack_push(new_input_handle_p, mode.analyser_function, IConvInputCodingName);
}

template <class InputHandle> inline void    
CLASS::include_stack_push(InputHandle*   new_input_handle_p, 
                          const int      MODE_ID /* = -1 */, 
                          const char*    IConvInputCodingName /* = 0x0 */)
{
    // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
    __quex_assert(    MODE_ID == -1 
                  || (MODE_ID >= 1 && MODE_ID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1));
    if( MODE_ID == -1 ) 
        __include_stack_push(new_input_handle_p, __current_mode_analyser_function_p, IConvInputCodingName); 
    else
        __include_stack_push(new_input_handle_p, mode_db[MODE_ID]->analyser_function, IConvInputCodingName);
}

template <class InputHandle> inline void    
CLASS::__include_stack_push(InputHandle*         new_input_handle_p, 
                            QUEX_MODE_FUNCTION_P StartModeAnalyzerFunction, 
                            const char*          IConvInputCodingName)
{
    __quex_assert(StartModeAnalyzerFunction != 0x0);
    __quex_assert(new_input_handle_p != 0x0);
    // IConvInputCodingName == 0x0 possible if normal ASCII is ment (e.g. no iconv support)

    _include_stack.push_back(CLASS::memento());
    CLASS::memento&  current = _include_stack.back();

    // (1) saving the current state of the lexical analyzer (memento pattern)
    current.buffer_p = this->__buffer;
    current.char_covered_by_terminating_zero = this->char_covered_by_terminating_zero;
    current.current_mode_analyser_function_p = this->__current_mode_analyser_function_p ;
    current.continue_analysis_after_adapting_mode_function_p_f = \
               this->__continue_analysis_after_adapting_mode_function_p_f;
#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    current.begin_of_line_f = this->begin_of_line_f; 
#   endif
    current.counter = this->counter;
    this->counter.init();

    // (2) initializing the new state of the lexer for reading the new input file/stream
    QUEX_CORE_BUFFER_TYPE* tmp = this->create_buffer(new_input_handle_p, IConvInputCodingName);
    QUEX_CORE_ANALYSER_STRUCT_init(this, 0, tmp, StartModeAnalyzerFunction);
}   

inline bool
CLASS::include_stack_pop() 
{
    if( _include_stack.empty() ) return false;

    CLASS::memento&  previous = _include_stack.back();

    delete this->__buffer;
    this->__buffer = previous.buffer_p;

    this->char_covered_by_terminating_zero    = previous.char_covered_by_terminating_zero;
    this->__current_mode_analyser_function_p  = previous.current_mode_analyser_function_p;
    this->__continue_analysis_after_adapting_mode_function_p_f = \
              previous.continue_analysis_after_adapting_mode_function_p_f;
#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    this->begin_of_line_f = previous.begin_of_line_f; 
#   endif
    this->counter = previous.counter;

    _include_stack.pop_back();

    return true;
}

