// -*- C++ -*-   vim: set syntax=cpp:

inline __QUEX_SETTING_TOKEN_CLASS_NAME::id_type
CLASS::get_token() 
{
    // The framework / constructor **should** ensure that at this point the two
    // pointers are identical. Since this function is called very often the
    // assignment of safety (prev=current) is not done. Instead, we only check
    // (as long as NDEBUG is not defined) that the framework assigns the variables
    // propperly.
    __quex_assert( self.__previous_mode_p == self.__current_mode_p );
    
    return __current_mode_analyser_function_p(this);
}

