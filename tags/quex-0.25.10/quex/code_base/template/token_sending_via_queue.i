// -*- C++ -*- vim:set syntax=cpp:

#ifdef QUEX_OPTION_DEBUG_TOKEN_SENDING
#   define __QUEX_DEBUG_TOKEN_SENDING() \
        std::cerr << "$$LEXER_CLASS_NAME$$::send " << *(_token_queue->top()) << std::endl;
#else
#   define __QUEX_DEBUG_TOKEN_SENDING() /* nothing */
#endif

inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME& That) 
{
    _token_queue->push(That);
    __QUEX_DEBUG_TOKEN_SENDING();
}

inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME::id_type ID) 
{
    _token_queue->push(ID);
    __QUEX_DEBUG_TOKEN_SENDING();
}

inline void   
CLASS::send_n(const int N, __QUEX_SETTING_TOKEN_CLASS_NAME::id_type ID) 
{
    __quex_assert(N > 0);
    for(int n=0; n < N; n++) send(ID); // applies DEBUG of 'send()'
}

template <typename ContentT>
inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME::id_type ID, ContentT Content) 
{
    _token_queue->push(ID, Content);
    __QUEX_DEBUG_TOKEN_SENDING();
}

#undef __QUEX_DEBUG_TOKEN_SENDING


