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
    
    do {
        __current_mode_analyser_function_p(this);

        // In case a mode change happend inside the pattern actions, the function is forced
        // to return (see end of analyzer function at REENTRY label). If the tokenstack is
        // non-empty, we return to the caller (spare one check). If its empty the analyzer
        // function (which has recently been setup) is called again.
        //
        if( __continue_analysis_after_adapting_mode_function_p_f ) {
            __continue_analysis_after_adapting_mode_function_p_f = false;
            continue;
        }
        break;
        
    } while( 1 + 1 == 2 );

    return _token.type_id();
}

