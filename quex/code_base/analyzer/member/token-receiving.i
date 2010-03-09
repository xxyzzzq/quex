/* -*- C++ -*-   vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_RECEIVING_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_RECEIVING_I

#ifndef QUEX_TYPE_ANALYZER
#   error "This file requires the macro 'QUEX_TYPE_ANALYZER' to be defined."
#endif

#include <quex/code_base/token/TokenPolicy>

QUEX_NAMESPACE_MAIN_OPEN

#   if ! defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
#      undef   QUEX_TOKEN_POLICY_NO_TOKEN
#      define  QUEX_TOKEN_POLICY_NO_TOKEN()       (false)
#   endif

#   define self (*me)
      
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
    QUEX_INLINE QUEX_TYPE_TOKEN* 
    QUEX_NAME(receive_p)(QUEX_TYPE_ANALYZER* me)
    { 
        register QUEX_TYPE_TOKEN* result_p = 0x0;

#       if defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)
        if( __QUEX_REPEATED_TOKEN_PRESENT(self_token_p()) ) {
            __QUEX_REPEATED_TOKEN_DECREMENT_N(self_token_p());
            return self_token_p();  
        } else
#       endif
        /* Tokens are in queue --> take next token from queue */ 
        if( QUEX_NAME(TokenQueue_is_empty)(&me->_token_queue) == false ) {        
            result_p = QUEX_NAME(TokenQueue_pop)(&me->_token_queue);
            return result_p;  
        } 

        /* Restart filling the queue from begin */
        QUEX_NAME(TokenQueue_reset)(&me->_token_queue);

        /* Analyze until there is some content in the queue */
        do {
            me->current_analyzer_function(me);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&me->_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        
        

#       if defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)
        result_p = me->_token_queue.read_iterator;
        if( __QUEX_SETTING_TOKEN_ID_REPETITION_TEST ) {
            QUEX_ASSERT_REPEATED_TOKEN_NOT_ZERO(result_p);
            /* First rep. is sent below. */
            if( QUEX_NAME_TOKEN(repetition_n_get)(result_p) == 1 ) {
                (void)QUEX_NAME(TokenQueue_pop)(&me->_token_queue);
            } else {
                __QUEX_REPEATED_TOKEN_DECREMENT_N(result_p); 
            }
            return result_p;
        } else 
#       endif
        {
            return QUEX_NAME(TokenQueue_pop)(&me->_token_queue);
        }
    }

#   elif defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)

    QUEX_INLINE  QUEX_TYPE_TOKEN_ID
    QUEX_NAME(receive)(QUEX_TYPE_ANALYZER* me) 
    {
        register QUEX_TYPE_TOKEN_ID __self_result_token_id = (QUEX_TYPE_TOKEN_ID)-1;

#       if defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)
        if( __QUEX_REPEATED_TOKEN_PRESENT(self_token_p()) ) {
            __QUEX_REPEATED_TOKEN_DECREMENT_N(self_token_p());
            return self_token_p()->_id;  
        }
#       endif

        __quex_assert(me->token != 0x0);
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        do {
            __self_result_token_id = me->current_analyzer_function(me);
            /* Currently it is necessary to check wether the return value
             * is appropriate, since event handlers may have set the token
             * identifier, without setting __self_result_token_id.         */
            if( __self_result_token_id != me->token->_id ) {
                __self_result_token_id = me->token->_id;
            }
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

#       if defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)
        if( __QUEX_SETTING_TOKEN_ID_REPETITION_TEST ) {
            QUEX_ASSERT_REPEATED_TOKEN_NOT_ZERO(self_token_p());
            __QUEX_REPEATED_TOKEN_DECREMENT_N(self_token_p()); /* First rep. is sent now. */
        }
#       endif

        return __self_result_token_id;
    }
#   else
#      error "Token policy must be 'queue' or 'users_token'."
#   endif

#ifndef __QUEX_OPTION_PLAIN_C
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE

    QUEX_INLINE QUEX_TYPE_TOKEN*
    QUEX_MEMBER(receive)() 
    { return QUEX_NAME(receive_p)(this); }

#   elif defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)

    QUEX_INLINE QUEX_TYPE_TOKEN_ID
    QUEX_MEMBER(receive)() 
    { return QUEX_NAME(receive)(this); }

#   else
#      error "Token policy must be 'queue' or 'users_token'."
#   endif
#endif

#   undef self

QUEX_NAMESPACE_MAIN_CLOSE
#endif
