// -*- C++ -*-   vim: set syntax=cpp:

namespace quex { 


#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
#   else
    inline void
#   endif
    CLASS::get_token(QUEX_TYPE_TOKEN* result_p) 
    {
    }

#   ifdef __QUEX_OPTION_ANALYZER_RETURNS_TOKEN_ID
    inline QUEX_TYPE_TOKEN_ID
#   else
    inline QUEX_TYPE_TOKEN
#   endif
    CLASS::get_token() 
    {
        // The framework / constructor **should** ensure that at this point the two
        // pointers are identical. Since this function is called very often the
        // assignment of safety (prev=current) is not done. Instead, we only check
        // (as long as NDEBUG is not defined) that the framework assigns the variables
        // propperly.
#       if ! defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
        return QuexAnalyser::current_analyser_function(this);
#       else
        QUEX_TYPE_TOKEN_ID token_id = __QUEX_TOKEN_ID_TERMINATION;
        do {
            token_id = QuexAnalyser::current_analyser_function(this);
        } while( token_id == __QUEX_TOKEN_ID_UNINITIALIZED );
        return token_id;
#       endif
    }
}
