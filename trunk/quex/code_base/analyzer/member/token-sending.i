/* -*- C++ -*-   vim: set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer                                */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I

#include <quex/code_base/token/TokenPolicy>
#include <quex/code_base/analyzer/member/token-sending>

QUEX_NAMESPACE_MAIN_OPEN

#   ifndef __QUEX_OPTION_PLAIN_C
    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN& That) 
    { 
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send(Token&)", 
                                                              "self_send_token()"));
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID) 
    { 
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send(TokenID)", 
                                                              "self_send(ID)"));
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send_n)(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
    { 
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send_n(TokenID)", 
                                                              "self_send_n(ID)"));
    }


    template <typename X0_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0) 
    {
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send()", 
                                                              "self_send1()"));
    }

    template <typename X0_T, typename X1_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1) 
    {
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send()", 
                                                              "self_send2()"));
    }

    template <typename X0_T, typename X1_T, typename X2_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2) 
    {
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send()", 
                                                              "self_send3()"));
    }

    template <typename X0_T, typename X1_T, typename X2_T, typename X3_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2, X3_T X3) 
    {
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send()", 
                                                              "self_send4()"));
    }
#   endif


#undef self

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_SENDING */
