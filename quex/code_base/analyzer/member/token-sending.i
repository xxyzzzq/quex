/* -*- C++ -*-   vim: set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer                                */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I

#ifndef QUEX_TYPE_ANALYZER
#   error "This file requires the macro 'QUEX_TYPE_ANALYZER' to be defined."
#endif

#include <quex/code_base/token/TokenPolicy>

QUEX_NAMESPACE_MAIN_OPEN

#   define self (*this)

#   ifndef __QUEX_SETTING_PLAIN_C
    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN& That) 
    { 
        self_send_token(That); 
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID) 
    { 
        self_send(ID); 
    }

    QUEX_INLINE void   
    QUEX_MEMBER(send_n)(const int RepetitionN, QUEX_TYPE_TOKEN_ID ID) 
    { 
        self_send_n(RepetitionN, ID); 
    }


    template <typename X0_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0) 
    {
        self_send1(ID, X0);
    }

    template <typename X0_T, typename X1_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1) 
    {
        self_send2(ID, X0, X1);
    }

    template <typename X0_T, typename X1_T, typename X2_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2) 
    {
        self_send3(ID, X0, X1, X2);
    }

    template <typename X0_T, typename X1_T, typename X2_T, typename X3_T> QUEX_INLINE void   
    QUEX_MEMBER(send)(const QUEX_TYPE_TOKEN_ID ID, X0_T X0, X1_T X1, X2_T X2, X3_T X3) 
    {
        self_send4(ID, X0, X1, X2, X3);
    }
#   endif


#undef self

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD__QUEX_LEXER_CLASS_TOKEN_SENDING */
