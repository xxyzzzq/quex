// -*- C++ -*-   vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
#define __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__

namespace quex { 

#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
#   else
    inline void
#   endif
    CLASS::get_token(QUEX_TYPE_TOKEN** result_pp) 
    // NOTE: As long as the 'get_token()' function is not called there is nothing
    //       happening to the token in the queue. But, a parser very probably
    //       does a couple af calls to 'get_token()' before a rule triggers 
    //       and data structures can be stored.
    //
    // ARGUMENTS:
    //     result_p  points to memory where token information has to be stored.
    // TIP:
    //     result_p could point into the token queue directly (TODO), if a limit 
    //     number can be defined so that the token queue does not overwrite it, as
    //     long as the parser is chewing on it.
    //
    // RETURNS:
    //    Token-ID of the currently read token.
    //    Token-ID = '$$TOKEN_CLASS$$::ID_UNITIALIZED' is returned in 
    //               case that no  token could be read.
    {
        __quex_assert(_token_queue != 0x0);
        // (i) tokens are in queue --> take next token from stack
        if( QuexTokenQueue_is_empty(_token_queue) == false ) {
            // DEBUG    
            *result_pp = QuexTokenQueue_pop(_token_queue);
            return;
        }

#       if ! defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
        QuexAnalyser::current_analyser_function(this);
#       else
        do { 
            QuexAnalyser::current_analyser_function(this);

            // In case a mode change happend inside the pattern actions, the function is forced
            // to return (see end of analyzer function at REENTRY label). If the tokenstack is
            // non-empty, we return to the caller (spare one check). If its empty the analyzer
            // function (which has recently been setup) is called again.
        } while ( QuexTokenQueue_is_empty(_token_queue) );
#       endif

        *result_pp = QuexTokenQueue_pop(_token_queue);
#       ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
        return (*result_pp)->type_id();
#       else
        return;
#       endif
    }


#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        QUEX_TYPE_TOKEN*   tmp = 0x0;
        QUEX_TYPE_TOKEN_ID type_id = get_token(&tmp);
        *result_p = *tmp;
        return type_id;
    }
#   else
    inline void
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        QUEX_TYPE_TOKEN*   tmp = 0x0;
        get_token(&tmp);
        *result_p = *tmp;
        return;
    }
#   endif


#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
    CLASS::get_token() 
    {
        QUEX_TYPE_TOKEN* tmp = 0x0;
        return get_token(&tmp);
    }
#   else
    inline QUEX_TYPE_TOKEN
    CLASS::get_token() 
    {
        QUEX_TYPE_TOKEN* tmp = 0x0;
        get_token(&tmp);
        return *tmp;
    }
#   endif
}

#endif // __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_QUEUE_I__
