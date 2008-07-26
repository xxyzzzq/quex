// -*- C++ -*- vim:set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__INCLUDE_STACK
#define __INCLUDE_GUARD__QUEX__INCLUDE_STACK

inline 
IncludeStack::IncludeStack(CLASS* the_lexer)
    : _the_lexer(the_lexer)
{ }


inline void
IncludeStack::memento::map_from_lexical_analyzer(CLASS* TheLexer)
{
    // (1) saving the current state of the lexical analyzer (memento pattern)
    this->buffer_p                         = TheLexer->__buffer;
    this->char_covered_by_terminating_zero = TheLexer->char_covered_by_terminating_zero;
    this->current_mode_analyser_function_p = TheLexer->__current_mode_analyser_function_p;
#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    this->begin_of_line_f                  = TheLexer->begin_of_line_f; 
#   endif
    this->counter                          = TheLexer->counter;
    this->continue_analysis_after_adapting_mode_function_p_f = \
               TheLexer->__continue_analysis_after_adapting_mode_function_p_f;
}

inline void
IncludeStack::memento::map_to_lexical_analyzer(CLASS* the_lexer)
{
    the_lexer->__buffer                            = this->buffer_p;
    the_lexer->char_covered_by_terminating_zero    = this->char_covered_by_terminating_zero;
    the_lexer->__current_mode_analyser_function_p  = this->current_mode_analyser_function_p;
#   ifdef __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    the_lexer->begin_of_line_f                     = this->begin_of_line_f; 
#   endif
    the_lexer->counter                             = this->counter;
    the_lexer->__continue_analysis_after_adapting_mode_function_p_f = \
              this->continue_analysis_after_adapting_mode_function_p_f;
}

template <class InputHandle> inline void    
IncludeStack::push(InputHandle*      new_input_handle_p, 
                   const quex_mode&  mode, 
                   const char*       IConvInputCodingName /* = 0x0 */)
{
    // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
    __push(new_input_handle_p, mode.analyser_function, IConvInputCodingName);
}

template <class InputHandle> inline void    
IncludeStack::push(InputHandle*   new_input_handle_p, 
                   const int      MODE_ID /* = -1 */, 
                   const char*    IConvInputCodingName /* = 0x0 */)
{
    // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
    __quex_assert(    MODE_ID == -1 
                  || (MODE_ID >= 1 && MODE_ID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1));
    if( MODE_ID == -1 ) 
        __push(new_input_handle_p, _the_lexer->__current_mode_analyser_function_p, IConvInputCodingName); 
    else
        __push(new_input_handle_p, _the_lexer->mode_db[MODE_ID]->analyser_function, IConvInputCodingName);
}

template <class InputHandle> inline void    
IncludeStack::__push(InputHandle*         new_input_handle_p, 
                     QUEX_MODE_FUNCTION_P StartModeAnalyzerFunction, 
                     const char*          IConvInputCodingName)
{
    __quex_assert(StartModeAnalyzerFunction != 0x0);
    __quex_assert(new_input_handle_p != 0x0);
    // IConvInputCodingName == 0x0 possible if normal ASCII is ment (e.g. no iconv support)

    _stack.push_back(memento());

    // (1) saving the current state of the lexical analyzer (memento pattern)
    _stack.back().map_from_lexical_analyzer(_the_lexer);

    _the_lexer->counter.init();

    // (2) initializing the new state of the lexer for reading the new input file/stream
    QUEX_CORE_BUFFER_TYPE* tmp = _the_lexer->create_buffer(new_input_handle_p, IConvInputCodingName);
    QUEX_CORE_ANALYSER_STRUCT_init(_the_lexer, 0, tmp, StartModeAnalyzerFunction);
}   

inline bool
IncludeStack::pop() 
{
    if( _stack.empty() ) return false;

    delete _the_lexer->__buffer;

    _stack.back().map_to_lexical_analyzer(_the_lexer);

    _stack.pop_back();

    return true;
}

#endif // __INCLUDE_GUARD__QUEX__INCLUDE_STACK
