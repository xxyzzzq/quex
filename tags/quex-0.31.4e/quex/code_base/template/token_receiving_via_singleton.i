// -*- C++ -*-   vim: set syntax=cpp:

namespace quex { 
    inline QUEX_TOKEN_ID_TYPE
    CLASS::get_token() 
    {
        // The framework / constructor **should** ensure that at this point the two
        // pointers are identical. Since this function is called very often the
        // assignment of safety (prev=current) is not done. Instead, we only check
        // (as long as NDEBUG is not defined) that the framework assigns the variables
        // propperly.
        return QuexAnalyser::current_analyser_function(this);
    }
}
