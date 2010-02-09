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
    QUEX_INLINE void
    QUEX_NAME(receive_pp)(QUEX_TYPE_ANALYZER* me,
                          QUEX_TYPE_TOKEN**   result_pp) 
    /* NOTE: As long as the 'receive()' function is not called there is nothing
     *       happening to the token in the queue. But, a parser very probably
     *       does a couple af calls to 'receive()' before a rule triggers 
     *       and data structures can be stored.
     *
     * ARGUMENTS:
     *     result_p  points to memory where token information has to be stored.
     * TIP:
     *     result_p could point into the token queue directly (TODO), if a limit 
     *     number can be defined so that the token queue does not overwrite it, as
     *     long as the parser is chewing on it.
     *
     * RETURNS:
     *    Token-ID of the currently read token.
     *    Token-ID = '$$TOKEN_CLASS$$::ID_UNITIALIZED' is returned in 
     *               case that no  token could be read.                                      */
    {
        /* Tokens are in queue --> take next token from queue                                */
        if( QUEX_NAME(TokenQueue_is_empty)(&me->_token_queue) == false ) {        
            *result_pp = QUEX_NAME(TokenQueue_pop)(&me->_token_queue);
            return;  
        } 
        else if( me->_token_queue.remaining_repetitions_of_last_token_n ) {
            --(me->_token_queue.remaining_repetitions_of_last_token_n);
            *result_pp = QUEX_NAME(TokenQueue_back)(&me->_token_queue);
            return;
        }

        /* Restart filling the queue from begin */
        QUEX_NAME(TokenQueue_reset)(&me->_token_queue);

        /* In case a mode change happend inside the pattern actions, the function is forced
         * to return (see end of analyzer function at REENTRY label). If the tokenstack is
         * non-empty, we return to the caller (spare one check). If its empty the analyzer
         * function (which has recently been setup) is called again.                        */
        do {
            me->current_analyzer_function(me);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&me->_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        *result_pp = QUEX_NAME(TokenQueue_pop)(&me->_token_queue);
        return;
    }

    QUEX_INLINE void
    QUEX_NAME(receive_p)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_TOKEN* result_p) 
    {
        /* Tokens are in queue --> take next token from queue                                */
        if( QUEX_NAME(TokenQueue_is_empty)(&me->_token_queue) == false ) {        
            QUEX_NAME_TOKEN(copy)(result_p, QUEX_NAME(TokenQueue_pop)(&me->_token_queue));
            return;  
        } 
        else if( me->_token_queue.remaining_repetitions_of_last_token_n ) {
            --(me->_token_queue.remaining_repetitions_of_last_token_n);
            QUEX_NAME_TOKEN(copy)(result_p, QUEX_NAME(TokenQueue_back)(&me->_token_queue));
            return;
        }

        /* Restart filling the queue from begin */
        QUEX_NAME(TokenQueue_reset)(&me->_token_queue);

        /* Analyze until there is some content in the queue */
        do {
            me->current_analyzer_function(me);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&me->_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        
        
        QUEX_NAME_TOKEN(copy)(result_p, QUEX_NAME(TokenQueue_pop)(&me->_token_queue));

        return;
    }
#   elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN)

    QUEX_INLINE void
    QUEX_NAME(receive_p)(QUEX_TYPE_ANALYZER*  me,
                         QUEX_TYPE_TOKEN*     result_p) 
    {
        me->token = result_p;
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        do {
            me->current_analyzer_function(me);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }

    QUEX_INLINE void
    QUEX_NAME(receive)(QUEX_TYPE_ANALYZER* me) 
    {
        __quex_assert(me->token != 0x0);
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        do {
            me->current_analyzer_function(me);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }

#   elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
    QUEX_INLINE QUEX_TYPE_TOKEN*
    QUEX_NAME(receive_to_array)(QUEX_TYPE_ANALYZER* me,
                                QUEX_TYPE_TOKEN* QueueMemoryBegin, QUEX_TYPE_TOKEN* QueueMemoryEnd) 
        /* RETURNS: Pointer to first token after the last filled in token. */
    {
        __quex_assert(QueueMemoryBegin != 0x0);
        __quex_assert(QueueMemoryEnd > QueueMemoryBegin);
        QUEX_NAME(TokenQueue_init)(&me->_token_queue, QueueMemoryBegin, QueueMemoryEnd,
                                   QUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER);

        do {
            me->current_analyzer_function(me);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&me->_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return me->_token_queue.write_iterator;
    }
#   endif

#ifndef __QUEX_OPTION_PLAIN_C
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
    QUEX_INLINE void
    QUEX_MEMBER(receive)(QUEX_TYPE_TOKEN**   result_pp) 
    { QUEX_NAME(receive_pp)(this, result_pp); }

    QUEX_INLINE void
    QUEX_MEMBER(receive)(QUEX_TYPE_TOKEN*   result_p) 
    { QUEX_NAME(receive_p)(this, result_p); }

#   elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN)
    QUEX_INLINE void
    QUEX_MEMBER(receive)() 
    { QUEX_NAME(receive)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(receive)(QUEX_TYPE_TOKEN*   result_p) 
    { QUEX_NAME(receive_p)(this, result_p); }

#   elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
    QUEX_INLINE QUEX_TYPE_TOKEN*
    QUEX_MEMBER(receive)(QUEX_TYPE_TOKEN* QueueMemoryBegin, QUEX_TYPE_TOKEN* QueueMemoryEnd) 
    { return QUEX_NAME(receive_to_array)(this, QueueMemoryBegin, QueueMemoryEnd); } 
#   endif
#endif

#   undef self

QUEX_NAMESPACE_MAIN_CLOSE
#endif
