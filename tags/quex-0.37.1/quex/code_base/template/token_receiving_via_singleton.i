// -*- C++ -*-   vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_SINGLETON_I__
#define __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_SINGLETON_I__

namespace quex { 


#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
    CLASS::get_token(QUEX_TYPE_TOKEN** result_pp) 
    {
        QuexAnalyser::current_analyser_function(this);
        *result_pp = this->token;
        return this->token->type_id();
    }
#   else
    inline void
    CLASS::get_token(QUEX_TYPE_TOKEN** result_pp) 
    {
        QuexAnalyser::current_analyser_function(this);
        *result_pp = this->token;
        return;
    }
#   endif

#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        QUEX_TYPE_TOKEN_ID type_id = QuexAnalyser::current_analyser_function(this);
        *result_p = *(this->token);
        return type_id;
    }
#   else
    inline void
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
        QuexAnalyser::current_analyser_function(this);
        *result_p = *(this->token);
        return;
    }
#   endif

#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
    CLASS::get_token() 
    {
        return QuexAnalyser::current_analyser_function(this);
    }
#   else
    inline QUEX_TYPE_TOKEN
    CLASS::get_token() 
    {
        QuexAnalyser::current_analyser_function(this);
        return *(this->token);
    }
#   endif
}

#endif // __INCLUDE_GUARD__QUEX__TOKEN_RECEIVING_VIA_SINGLETON_I__
