// -*- C++ -*- vim:set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__INCLUDE_STACK
#define __INCLUDE_GUARD__QUEX__INCLUDE_STACK

inline 
IncludeStack::IncludeStack(CLASS* the_lexer)
    : _the_lexer(the_lexer)
{ }


template <class InputHandle> inline void    
IncludeStack::push(InputHandle*     new_input_handle_p, 
                   const QuexMode&  mode, 
                   const char*      IANA_CodingName /* = 0x0 */)
{
    // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
    __push(new_input_handle_p, mode.analyser_function, IANA_CodingName);
}

template <class InputHandle> inline void    
IncludeStack::push(InputHandle*   new_input_handle_p, 
                   const int      MODE_ID /* = -1 */, 
                   const char*    IANA_CodingName /* = 0x0 */)
{
    // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
    __quex_assert(    MODE_ID == -1 
                  || (MODE_ID >= 1 && MODE_ID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1));
    if( MODE_ID == -1 ) 
        __push(new_input_handle_p, _the_lexer->__current_mode_analyser_function_p, IANA_CodingName); 
    else
        __push(new_input_handle_p, _the_lexer->mode_db[MODE_ID]->analyser_function, IANA_CodingName);
}

template <class InputHandle> inline void    
IncludeStack::__push(InputHandle*         new_input_handle_p, 
                     QUEX_MODE_FUNCTION_P StartModeAnalyzerFunction, 
                     const char*          IANA_CodingName)
{
    __quex_assert(StartModeAnalyzerFunction != 0x0);
    __quex_assert(new_input_handle_p != 0x0);
    // IANA_CodingName == 0x0 possible if normal ASCII is ment (e.g. no iconv support)

    _stack.push_back(memento());

    // (1) saving the current state of the lexical analyzer (memento pattern)
    _stack.back().map_from_lexical_analyzer(_the_lexer);

    _the_lexer->counter.init();

    // (2) initializing the new state of the lexer for reading the new input file/stream
    QUEX_CORE_QuexBuffer* tmp = _the_lexer->create_buffer(new_input_handle_p, IANA_CodingName);
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

inline void
IncludeStack::memento::map_from_lexical_analyzer(CLASS* TheLexer)
{
    // (1) saving the current state of the lexical analyzer (memento pattern)
    this->base    = *((QuexAnalyser*)TheLexer);
    this->counter = TheLexer->counter;
}

inline void
IncludeStack::memento::map_to_lexical_analyzer(CLASS* the_lexer)
{
    // (1) saving the current state of the lexical analyzer (memento pattern)
    *((QuexAnalyser*)the_lexer) = this->base;
    the_lexer->counter          = this->counter;
}

#endif // __INCLUDE_GUARD__QUEX__INCLUDE_STACK
