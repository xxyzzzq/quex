
#include<noname>
namespace quex {
#define self  (*me)

    QUEX_ANALYSER_RETURN_TYPE 
    noname_uncallable_analyser_function(noname* me)
    { assert(0); return (QUEX_ANALYSER_RETURN_TYPE)(0); }

    void 
    noname_on_indentation_null_function(noname*, const int)
    {}
    
    void 
    noname_on_entry_exit_null_function(noname*, const quex_mode*)
    {}

    void
    noname__START_on_entry(noname* me, const quex_mode* FromMode) {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->START.has_entry_from(FromMode));
#endif

    }
    void
    noname__START_on_exit(noname* me, const quex_mode* ToMode)  {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->START.has_exit_to(ToMode));
#endif

    }

#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT        
    void
    noname__START_on_indentation(noname* me, const int Indentation) {
assert(Indentation >= 0);
    }
#endif

#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    bool
    noname__START_has_base(const quex_mode* Mode) {
    return false;
    }
    bool
    noname__START_has_entry_from(const quex_mode* Mode) {
    return true; // default
    }
    bool
    noname__START_has_exit_to(const quex_mode* Mode) {
    return true; // default
    }
#endif    
#undef self
} // END: namespace quex
