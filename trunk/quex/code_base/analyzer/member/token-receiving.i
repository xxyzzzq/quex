/* -*- C++ -*-   vim: set syntax=cpp:
 *
 * NO INCLUDE GUARDS -- THIS FILE MIGHT BE INCLUDED TWICE FOR MULTIPLE
 *                      LEXICAL ANALYZERS
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_RECEIVE
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_RECEIVE            */
#ifndef QUEX_TYPE_ANALYZER
#   error "This file requires the macro 'QUEX_TYPE_ANALYZER' to be defined."
#endif

#include <quex/code_base/token/TokenPolicy>

QUEX_NAMESPACE_MAIN_OPEN

#   if ! defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
#      undef   QUEX_TOKEN_POLICY_NO_TOKEN
#      define  QUEX_TOKEN_POLICY_NO_TOKEN()       (false)
#   endif

#   define self (*this)
      
#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, receive)(__QUEX_SETTING_THIS_POINTER
                                    QUEX_TYPE_TOKEN_WITH_NAMESPACE** result_pp) 
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
        if( QUEX_TYPE_TOKEN_QUEUE_is_empty(_token_queue) == false ) {        
            *result_pp = QUEX_TYPE_TOKEN_QUEUE_pop(_token_queue);
            return;  
        } 
        else if( _token_queue.remaining_repetitions_of_last_token_n ) {
            --(_token_queue.remaining_repetitions_of_last_token_n);
            *result_pp = QUEX_TYPE_TOKEN_QUEUE_back(_token_queue);
            return;
        }

        /* Restart filling the queue from begin */
        QUEX_TYPE_TOKEN_QUEUE_reset(_token_queue);

        /* In case a mode change happend inside the pattern actions, the function is forced
         * to return (see end of analyzer function at REENTRY label). If the tokenstack is
         * non-empty, we return to the caller (spare one check). If its empty the analyzer
         * function (which has recently been setup) is called again.                        */
        do {
            engine.current_analyzer_function((QUEX_TYPE_ANALYZER_DATA*)this);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        *result_pp = QUEX_TYPE_TOKEN_QUEUE_pop(_token_queue);
        return;
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, receive)(__QUEX_SETTING_THIS_POINTER
                                    QUEX_TYPE_TOKEN_WITH_NAMESPACE* result_p) 
    {
        /* Tokens are in queue --> take next token from queue                                */
        if( QUEX_TYPE_TOKEN_QUEUE_is_empty(_token_queue) == false ) {        
            result_p->__copy(*(QUEX_TYPE_TOKEN_QUEUE_pop(_token_queue)));
            return;  
        } 
        else if( _token_queue.remaining_repetitions_of_last_token_n ) {
            --(_token_queue.remaining_repetitions_of_last_token_n);
            result_p->__copy(*(QUEX_TYPE_TOKEN_QUEUE_back(_token_queue)));
            return;
        }

        /* Restart filling the queue from begin */
        QUEX_TYPE_TOKEN_QUEUE_reset(_token_queue);

        /* Analyze until there is some content in the queue */
        do {
            engine.current_analyzer_function((QUEX_TYPE_ANALYZER_DATA*)this);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        
        
        result_p->__copy(*QUEX_TYPE_TOKEN_QUEUE_pop(_token_queue));

        return;
    }
#   elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN)

    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, receive)(__QUEX_SETTING_THIS_POINTER
                                              QUEX_TYPE_TOKEN_WITH_NAMESPACE* result_p) 
    {
        this->token = result_p;
        this->token->set(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        do {
            engine.current_analyzer_function((QUEX_TYPE_ANALYZER_DATA*)this);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, receive)(__QUEX_SETTING_THIS_POINTER) 
    {
        __quex_assert(this->token != 0x0);

        this->token->set(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        do {
            engine.current_analyzer_function((QUEX_TYPE_ANALYZER_DATA*)this);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return;
    }
#   endif

#   if defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
    QUEX_INLINE QUEX_TYPE_TOKEN_WITH_NAMESPACE*
    QUEX_MEMFUNC(ANALYZER, receive)(__QUEX_SETTING_THIS_POINTER
                                              QUEX_TYPE_TOKEN_WITH_NAMESPACE* QueueMemoryBegin, QUEX_TYPE_TOKEN_WITH_NAMESPACE* QueueMemoryEnd) 
        /* RETURNS: Pointer to first token after the last filled in token. */
    {
        __quex_assert(QueueMemoryBegin != 0x0);
        __quex_assert(QueueMemoryEnd > QueueMemoryBegin);
        QUEX_TYPE_TOKEN_QUEUE_init(_token_queue, QueueMemoryBegin, QueueMemoryEnd,
                                   QUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER);

        do {
            engine.current_analyzer_function((QUEX_TYPE_ANALYZER_DATA*)this);
            QUEX_ASSERT_TOKEN_QUEUE_AFTER_WRITE(&_token_queue);
        } while( QUEX_TOKEN_POLICY_NO_TOKEN() );        

        return _token_queue.write_iterator;
    }
#   endif

#   undef self

QUEX_NAMESPACE_MAIN_CLOSE

