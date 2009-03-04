// -*- C++ -*- vim:set syntax=cpp:
namespace quex { 
#ifdef QUEX_OPTION_DEBUG_TOKEN_SENDING
#   define __QUEX_DEBUG_TOKEN_SENDING() \
        std::cerr << "$$LEXER_CLASS_NAME$$::send " << *(_token_queue->top()) << std::endl;
#else
#   define __QUEX_DEBUG_TOKEN_SENDING() /* nothing */
#endif

inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME& That) 
{
    QuexTokenQueue_push(_token_queue, That);
    __QUEX_DEBUG_TOKEN_SENDING();
}

inline void   
CLASS::send(const QUEX_TYPE_TOKEN_ID ID) 
{
    QuexTokenQueue_push1(_token_queue, ID);
    __QUEX_DEBUG_TOKEN_SENDING();
}

inline void   
CLASS::send_n(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
{
    __quex_assert(N > 0);
    const int AvailableN = QuexTokenQueue_available_n(me);
    const int N = N > AvailableN ? AvailableN : N;

    for(int n=0; n < N; n++) send(ID); // applies DEBUG of 'send()'
}

template <typename ContentT>
inline void   
CLASS::send(const QUEX_TYPE_TOKEN_ID ID, ContentT Content) 
{
    QuexTokenQueue_push2(_token_queue, ID, Content);
    __QUEX_DEBUG_TOKEN_SENDING();
}

} // namespace quex

#undef __QUEX_DEBUG_TOKEN_SENDING


