// -*- C++ -*- vim:set syntax=cpp:
namespace quex { 
#ifdef QUEX_OPTION_DEBUG_TOKEN_SENDING
#   define __QUEX_DEBUG_TOKEN_SENDING() \
        std::cerr << "$$LEXER_CLASS_NAME$$::send " << *(_token_queue->top()) << std::endl;
#else
#   define __QUEX_DEBUG_TOKEN_SENDING() /* nothing */
#endif

inline void   
CLASS::send(const QUEX_TYPE_TOKEN& That) 
{
    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);

    QuexTokenQueue_push(_token_queue, That);
    __QUEX_DEBUG_TOKEN_SENDING();

    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);
}

inline void   
CLASS::send(const QUEX_TYPE_TOKEN_ID ID) 
{
    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);

    QuexTokenQueue_push1(_token_queue, ID);
    __QUEX_DEBUG_TOKEN_SENDING();

    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);
}

inline void   
CLASS::send_n(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
{
    const int AvailableN = QuexTokenQueue_available_n(_token_queue);
    const int N = N > AvailableN ? AvailableN : N;
    __quex_assert(N > 0);

    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);

    for(int n=0; n < N; n++) {
        QuexTokenQueue_push1(_token_queue, ID);
    }
    _token_queue->remaining_repetitions_of_last_token_n = N - AvailableN;

    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);
}

template <typename ContentT>
inline void   
CLASS::send(const QUEX_TYPE_TOKEN_ID ID, ContentT Content) 
{
    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);

    QuexTokenQueue_push2(_token_queue, ID, Content);
    __QUEX_DEBUG_TOKEN_SENDING();

    QUEX_TOKEN_QUEUE_ASSERT(_token_queue);
}

} // namespace quex

#undef __QUEX_DEBUG_TOKEN_SENDING


