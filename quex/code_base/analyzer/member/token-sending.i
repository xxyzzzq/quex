/* -*- C++ -*-   vim: set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer                                */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I

#ifndef QUEX_TYPE_ANALYZER
#   error "This file requires the macro 'QUEX_TYPE_ANALYZER' to be defined."
#endif

#include <quex/code_base/token/TokenPolicy>

QUEX_NAMESPACE_MAIN_OPEN

#ifdef     __QUEX_OPTION_TOKEN_POLICY_IS_QUEUE_BASED
#   define __QUEX_ASSERT_SEND_ENTRY() \
           QUEX_TOKEN_QUEUE_ASSERT(&self._token_queue); \
           QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION);
#else
#   define __QUEX_ASSERT_SEND_ENTRY() \
           QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION(__QUEX_SETTING_TOKEN_ID_TERMINATION);
#endif

#   define self (*this)

    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN& That) 
    {
        __QUEX_ASSERT_SEND_ENTRY();
        QUEX_TOKEN_POLICY_SET(That);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID) 
    {
        __QUEX_ASSERT_SEND_ENTRY();
        QUEX_TOKEN_POLICY_SET_1(ID);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send_n)(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
    {
#       ifdef     __QUEX_OPTION_TOKEN_POLICY_IS_QUEUE_BASED
        const int AvailableN = QUEX_NAME(TokenQueue_available_n)(&_token_queue);
        const int N = RepetitionN > AvailableN ? AvailableN : RepetitionN;
        __quex_assert(N > 0);

        for(int n=0; n < N; n++) {
            __QUEX_ASSERT_SEND_ENTRY();
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

#   define self_send1(ID, X0)                        \
    do {                                             \
        __QUEX_ASSERT_SEND_ENTRY();                  \
        QUEX_TOKEN_POLICY_SET_2(ID, X0);             \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();            \
    } while ( 0 )

#   define self_send2(ID, X0, X1)                    \
    do {                                             \
        __QUEX_ASSERT_SEND_ENTRY();                  \
        QUEX_TOKEN_POLICY_SET_3(ID, X0, X1);         \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();            \
    } while ( 0 )

#   define self_send3(ID, X0, X1, X2)                \
    do {                                             \
        __QUEX_ASSERT_SEND_ENTRY();                  \
        QUEX_TOKEN_POLICY_SET_4(ID, X0, X1, X2);     \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();            \
    } while ( 0 )

#   define self_send4(ID, X0, X1, X2, X3)            \
    do {                                             \
        __QUEX_ASSERT_SEND_ENTRY();                  \
        QUEX_TOKEN_POLICY_SET_5(ID, X0, X1, X2, X3); \
        QUEX_TOKEN_POLICY_PREPARE_NEXT();            \
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

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_SENDING */
