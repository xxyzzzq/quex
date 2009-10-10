/* -*- C++ -*-   vim: set syntax=cpp:
 *
 * NO INCLUDE GUARDS -- THIS FILE MIGHT BE INCLUDED TWICE FOR MULTIPLE
 *                      LEXICAL ANALYZERS
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_SENDING
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_SENDING            */
#ifndef QUEX_TYPE_ANALYZER
#   error "This file requires the macro 'QUEX_TYPE_ANALYZER' to be defined."
#endif

#include <quex/code_base/token/TokenPolicy>

#ifndef __QUEX_SETTING_PLAIN_C
namespace quex { 
#endif

#   define self (*this)

    QUEX_INLINE void   
    QUEX_MEMFUNC(ANALYZER, send)(const QUEX_TYPE_TOKEN_WITH_NAMESPACE& That) 
    {
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION);
        QUEX_TOKEN_POLICY_SET(That);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    QUEX_INLINE void   
    QUEX_MEMFUNC(ANALYZER, send)(const QUEX_TYPE_TOKEN_ID ID) 
    {
        // self._token_queue->write_iterator->set(ID);
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION);
        QUEX_TOKEN_POLICY_SET_1(ID);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    QUEX_INLINE void   
    QUEX_MEMFUNC(ANALYZER, send_n)(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
    {
#       if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE) || defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
        const int AvailableN = QuexTokenQueue_available_n(_token_queue);
        const int N = RepetitionN > AvailableN ? AvailableN : RepetitionN;
        __quex_assert(N > 0);
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION);

        QUEX_TOKEN_QUEUE_ASSERT(&_token_queue);

        for(int n=0; n < N; n++) {
            QUEX_TOKEN_POLICY_SET_1(ID);
            QUEX_TOKEN_POLICY_PREPARE_NEXT();
        }
        if( N - AvailableN ) {
            _token_queue.remaining_repetitions_of_last_token_n = N - AvailableN;
        }
#       else
        QUEX_TOKEN_POLICY_SET_1(ID);
#       endif
    }


#   define self_send(ID) 

#   define self_send1(ID, X0) \
    do {                                                                                           \
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION); \
        QUEX_TOKEN_POLICY_SET_2(ID, X0);                                                           \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();                                                          \
    } while ( 0 )

#   define self_send2(ID, X0, X1) \
    do {                                                                                           \
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION); \
        QUEX_TOKEN_POLICY_SET_3(ID, X0, X1);                                                       \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();                                                          \
    } while ( 0 )

#   define self_send3(ID, X0, X1, X2) \
    do {                                                                                           \
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION); \
        QUEX_TOKEN_POLICY_SET_4(ID, X0, X1, X2);                                                   \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();                                                          \
    } while ( 0 )

#   define self_send4(ID, X0, X1, X2, X3) \
    do {                                                                                           \
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION); \
        QUEX_TOKEN_POLICY_SET_5(ID, X0, X1, X2, X3);                                               \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();                                                          \
    } while ( 0 )

#   ifndef __QUEX_SETTING_PLAIN_C
    template <typename X0_T> QUEX_INLINE void   
    QUEX_TYPE_ANALYZER::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0) 
    {
        self_send1(ID, X0);
    }

    template <typename X0_T, typename X1_T> QUEX_INLINE void   
    QUEX_TYPE_ANALYZER::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1) 
    {
        self_send2(ID, X0, X1);
    }

    template <typename X0_T, typename X1_T, typename X2_T> QUEX_INLINE void   
    QUEX_TYPE_ANALYZER::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2) 
    {
        self_send3(ID, X0, X1, X2);
    }

    template <typename X0_T, typename X1_T, typename X2_T, typename X3_T> QUEX_INLINE void   
    QUEX_TYPE_ANALYZER::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2, X3_T X3) 
    {
        self_send4(ID, X0, X1, X2, X3);
    }
#   endif


#undef self

#ifndef __QUEX_SETTING_PLAIN_C
} /* namespace quex { */
#endif

