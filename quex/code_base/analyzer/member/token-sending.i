/* -*- C++ -*-   vim: set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer                                */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I

#include <quex/code_base/token/TokenPolicy>
#include <quex/code_base/analyzer/member/token-sending>

QUEX_NAMESPACE_MAIN_OPEN

#   ifndef __QUEX_OPTION_PLAIN_C
    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID) 
    { 
        self_send(ID);
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send_n)(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
    { 
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_MEMBER_FUNC_DEPRECATED(".send_n(TokenID)", 
                                                              "self_send_n(ID)"));
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, QUEX_TYPE_CHARACTER* StrBegin) 
    {
        self_send1(ID, StrBegin);
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID  ID, 
                      QUEX_TYPE_CHARACTER*      X0, 
                      QUEX_TYPE_CHARACTER*      X1) 
    {
        self_send2(ID, StrBegin, StrEnd);
    }
#   endif


#undef self

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_SENDING */
