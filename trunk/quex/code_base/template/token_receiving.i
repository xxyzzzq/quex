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
    CLASS::get_token(QUEX_TYPE_TOKEN** result_pp) 
    /* NOTE: As long as the 'get_token()' function is not called there is nothing
     *       happening to the token in the queue. But, a parser very probably
     *       does a couple af calls to 'get_token()' before a rule triggers 
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
        /* (i) tokens are in queue --> take next token from stack                            */
        QUEX_TOKEN_POLICY_RETURN_ON_GET_TOKEN_FROM_QUEUE(*result_pp);

        /* In case a mode change happend inside the pattern actions, the function is forced
         * to return (see end of analyzer function at REENTRY label). If the tokenstack is
         * non-empty, we return to the caller (spare one check). If its empty the analyzer
         * function (which has recently been setup) is called again.                        */
        do   QuexAnalyser::current_analyser_function(this);
        while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        *result_pp = QuexTokenQueue_pop(_token_queue);
        return;
    }
#   endif /* QUEX_OPTION_TOKEN_POLICY_QUEUE */

#   if   defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
    inline void
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        QUEX_TOKEN_POLICY_RETURN_ON_GET_TOKEN_FROM_QUEUE(result_p);

        do   QuexAnalyser::current_analyser_function(this);
        while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        *result_p = *QuexTokenQueue_pop(_token_queue);

        return;
    }
#   elif defined(QUEX_OPTION_TOKEN_POLICY_SINGLETON)
    inline void
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        this->token = result_p;
        do   QuexAnalyser::current_analyser_function(this);
        while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }
#   endif


#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLETON)
    inline void
    CLASS::get_token() 
    {
        __quex_assert(this->token != 0x0);

        do   QuexAnalyser::current_analyser_function(this);
        while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }
#   endif

}

#endif // __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
