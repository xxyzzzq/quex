#include"lexer"
namespace quex {
        QuexMode  lexer::X;
#define self  (*me)

    void
    lexer_X_on_entry(lexer* me, const QuexMode* FromMode) {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
__quex_assert(me->X.has_entry_from(FromMode));
#endif

    }

    void
    lexer_X_on_exit(lexer* me, const QuexMode* ToMode)  {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
__quex_assert(me->X.has_exit_to(ToMode));
#endif

    }

#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT        
    void
    lexer_X_on_indentation(lexer* me, const int Indentation) {
__quex_assert(Indentation >= 0);
    }
#endif

#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    bool
    lexer_X_has_base(const QuexMode* Mode) {
    return false;
    }
    bool
    lexer_X_has_entry_from(const QuexMode* Mode) {
    return true; // default
    }
    bool
    lexer_X_has_exit_to(const QuexMode* Mode) {
    return true; // default
    }
#endif    
#undef self
} // END: namespace quex
