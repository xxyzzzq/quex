// -*- C++ -*- vim:set syntax=cpp:
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__QUEX_TOKEN_SENDING_H__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__QUEX_TOKEN_SENDING_H__

#include <quex/code_base/template/TokenPolicy>

namespace quex { 

    inline void   
    CLASS::send(const QUEX_TYPE_TOKEN& That) 
    {
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();
        QUEX_TOKEN_POLICY_SET(That);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    inline void   
    CLASS::send(const QUEX_TYPE_TOKEN_ID ID) 
    {
        // self._token_queue->write_iterator->set(ID);
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();
        QUEX_TOKEN_POLICY_SET_1(ID);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    template <typename X0_T> inline void   
    CLASS::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0) 
    {
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();
        QUEX_TOKEN_POLICY_SET_2(ID, X0);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    template <typename X0_T, typename X1_T> inline void   
    CLASS::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1) 
    {
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();
        QUEX_TOKEN_POLICY_SET_3(ID, X0, X1);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    template <typename X0_T, typename X1_T, typename X2_T> inline void   
    CLASS::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2) 
    {
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();
        QUEX_TOKEN_POLICY_SET_4(ID, X0, X1, X2);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    template <typename X0_T, typename X1_T, typename X2_T, typename X3_T> inline void   
    CLASS::send(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2, X3_T X3) 
    {
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();
        QUEX_TOKEN_POLICY_SET_5(ID, X0, X1, X2, X3);
        QUEX_TOKEN_POLICY_PREPARE_NEXT();
    }

    inline void   
    CLASS::send_n(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
    {
#       if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE) || defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
        const int AvailableN = QuexTokenQueue_available_n(_token_queue);
        const int N = RepetitionN > AvailableN ? AvailableN : RepetitionN;
        __quex_assert(N > 0);
        QUEX_ASSERT_NO_TOKEN_SENDING_AFTER_TOKEN_TERMINATION();

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

}

#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__QUEX_TOKEN_SENDING_H__ */
