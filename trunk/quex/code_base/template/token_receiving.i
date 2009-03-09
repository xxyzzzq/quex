// -*- C++ -*-   vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
#define __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__

namespace quex { 

#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
#      define __QUEX_RETURN_TYPE              QUEX_TYPE_TOKEN_ID
#      define __QUEX_RETURN_THIS(TOKEN_ID)    return (TOKEN_ID);
#      define __QUEX_REENTRY_CONDITION        (QuexTokenQueue_is_empty(_token_queue))
#      define __QUEX_TOKEN_ID_VAR_DEF(VAR)    QUEX_TYPE_TOKEN_ID   VAR    
#      define __QUEX_ANALYZER_CALL(VAR)       VAR = QuexAnalyser::current_analyser_function(this)

#   else
#      define __QUEX_RETURN_TYPE              void
#      define __QUEX_RETURN_THIS(TOKEN_ID)    return (TOKEN_ID);
#      define __QUEX_REENTRY_CONDITION        (token->type_id() == __QUEX_TOKEN_ID_UNINITIALIZED)
#      define __QUEX_TOKEN_ID_VAR_DEF(VAR)    /* type_id not used */
#      define __QUEX_ANALYZER_CALL(VAR)       QuexAnalyser::current_analyser_function(this)

#   endif

#   if ! defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
#      undef   __QUEX_REENTRY_CONDITION
#      define  __QUEX_REENTRY_CONDITION       (false)
#   endif

#   ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE
#      define __QUEX_TRY_TO_GET_TOKEN_FROM_QUEUE_AND_RETURN(TOKEN_P)          \
              if( QuexTokenQueue_is_empty(_token_queue) == false ) {          \
                 TOKEN_P = QuexTokenQueue_pop(_token_queue);                  \
                 __QUEX_RETURN_THIS((*result_pp)->type_id());                 \
              }                                                               \
              else if( token_queue->remaining_repetitions_of_last_token_n ) { \
                 --(token_queue->remaining_repetitions_of_last_token_n)       \
                 TOKEN_P = QuexTokenQueue_back(_token_queue);                 \
                 __QUEX_RETURN_THIS(token->type_id());                        \
              }
#   else
#      define __QUEX_TRY_TO_GET_TOKEN_FROM_QUEUE_AND_RETURN(TOKEN_P) \
              /* nothing */
#   endif
      
#   ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE
    inline __QUEX_RETURN_TYPE
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
        __QUEX_TOKEN_ID_VAR_DEF(type_id);

        /* (i) tokens are in queue --> take next token from stack                            */
        __QUEX_TRY_TO_GET_TOKEN_FROM_QUEUE_AND_RETURN(**result_pp);

        /* In case a mode change happend inside the pattern actions, the function is forced
         * to return (see end of analyzer function at REENTRY label). If the tokenstack is
         * non-empty, we return to the caller (spare one check). If its empty the analyzer
         * function (which has recently been setup) is called again.                        */
        do     __QUEX_ANALYZER_CALL(type_id); 
        while( __QUEX_REENTRY_CONDITION );        

        *result_pp = QuexTokenQueue_pop(_token_queue);
        __QUEX_RETURN_THIS((*result_pp)->type_id()); 
    }
#   endif /* QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE */

    inline __QUEX_RETURN_TYPE
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        QUEX_TYPE_TOKEN*   tmp = 0x0;
        __QUEX_TOKEN_ID_VAR_DEF(type_id);

        __QUEX_TRY_TO_GET_TOKEN_FROM_QUEUE_AND_RETURN();

        do     __QUEX_ANALYZER_CALL(type_id); 
        while( __QUEX_REENTRY_CONDITION );        

        *result_p = *tmp;

        __QUEX_RETURN_THIS(type_id);
    }


    inline __QUEX_RETURN_TYPE
    CLASS::get_token() 
    {
        QUEX_TYPE_TOKEN*   tmp = 0x0;
        __QUEX_TOKEN_ID_VAR_DEF(type_id);

        __QUEX_TRY_TO_GET_TOKEN_FROM_QUEUE_AND_RETURN();

        do     __QUEX_ANALYZER_CALL(type_id); 
        while( __QUEX_REENTRY_CONDITION );        

        __QUEX_RETURN_THIS(type_id);
    }
}

#undef __QUEX_RETURN_TYPE
#undef __QUEX_RETURN_THIS
#undef __QUEX_REENTRY_CONDITION
#undef __QUEX_TOKEN_ID_VAR_DEF
#undef __QUEX_ANALYZER_CALL
#undef __QUEX_TRY_TO_GET_TOKEN_FROM_QUEUE_AND_RETURN

#endif // __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
