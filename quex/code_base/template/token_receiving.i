// -*- C++ -*-   vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
#define __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__

#include <quex/code_base/template/TokenPolicy>

namespace quex { 

#   if ! defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
#      undef   QUEX_TOKEN_POLICY_NO_TOKEN
#      define  QUEX_TOKEN_POLICY_NO_TOKEN()       (false)
#   endif
      
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
    inline void
    CLASS::receive(QUEX_TYPE_TOKEN** result_pp) 
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
        if( QuexTokenQueue_is_empty(_token_queue) == false ) {        
            *result_pp = QuexTokenQueue_pop(_token_queue);
            return;  
        } 
        else if( _token_queue.remaining_repetitions_of_last_token_n ) {
            --(_token_queue.remaining_repetitions_of_last_token_n);
            *result_pp = QuexTokenQueue_back(_token_queue);
            return;
        }

        /* Restart filling the queue from begin */
        QuexTokenQueue_reset(_token_queue);

        /* In case a mode change happend inside the pattern actions, the function is forced
         * to return (see end of analyzer function at REENTRY label). If the tokenstack is
         * non-empty, we return to the caller (spare one check). If its empty the analyzer
         * function (which has recently been setup) is called again.                        */
        do {
            QuexAnalyser::current_analyser_function(this);
            QUEX_TOKEN_QUEUE_ASSERT(&_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        *result_pp = QuexTokenQueue_pop(_token_queue);
        return;
    }

    inline void
    CLASS::receive(QUEX_TYPE_TOKEN* result_p) 
    {
        /* Tokens are in queue --> take next token from queue                                */
        if( QuexTokenQueue_is_empty(_token_queue) == false ) {        
            *result_p = *(QuexTokenQueue_pop(_token_queue));
            return;  
        } 
        else if( _token_queue.remaining_repetitions_of_last_token_n ) {
            --(_token_queue.remaining_repetitions_of_last_token_n);
            *result_p = *(QuexTokenQueue_back(_token_queue));
            return;
        }

        /* Restart filling the queue from begin */
        QuexTokenQueue_reset(_token_queue);

        /* Analyze until there is some content in the queue */
        do {
            QuexAnalyser::current_analyser_function(this);
            QUEX_TOKEN_QUEUE_ASSERT(&_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        
        
        *result_p = *QuexTokenQueue_pop(_token_queue);

        return;
    }
#   elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN)

    inline void
    CLASS::receive(QUEX_TYPE_TOKEN* result_p) 
    {
        this->token = result_p;
        this->token->set(__QUEX_TOKEN_ID_UNINITIALIZED);
        do   QuexAnalyser::current_analyser_function(this);
        while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }

    inline void
    CLASS::receive() 
    {
        __quex_assert(this->token != 0x0);

        this->token->set(__QUEX_TOKEN_ID_UNINITIALIZED);
        do   QuexAnalyser::current_analyser_function(this);
        while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }
#   endif

#   if defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
    inline QUEX_TYPE_TOKEN*
    CLASS::receive(QUEX_TYPE_TOKEN* QueueMemoryBegin, QUEX_TYPE_TOKEN* QueueMemoryEnd) 
        /* RETURNS: Pointer to first token after the last filled in token. */
    {
        __quex_assert(QueueMemoryBegin != 0x0);
        __quex_assert(QueueMemoryEnd > QueueMemoryBegin);
        QuexTokenQueue_init(_token_queue, QueueMemoryBegin, QueueMemoryEnd);

        do {
            QuexAnalyser::current_analyser_function(this);
            QUEX_TOKEN_QUEUE_ASSERT(&_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return _token_queue.write_iterator;
    }
#   endif

}

#endif // __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
