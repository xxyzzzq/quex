#include<lexer>
namespace quex {
#define self  (*me)

    QUEX_ANALYSER_RETURN_TYPE 
    lexer_uncallable_analyser_function(lexer* me)
    { assert(0); return (QUEX_ANALYSER_RETURN_TYPE)(0); }

    void 
    lexer_on_indentation_null_function(lexer*, const int)
    {}
    
    void 
    lexer_on_entry_exit_null_function(lexer*, const quex_mode*)
    {}

    void
    lexer__END_OF_FILE_on_entry(lexer* me, const quex_mode* FromMode) {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->END_OF_FILE.has_entry_from(FromMode));
#endif

    }
    void
    lexer__END_OF_FILE_on_exit(lexer* me, const quex_mode* ToMode)  {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->END_OF_FILE.has_exit_to(ToMode));
#endif

    }

#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT        
    void
    lexer__END_OF_FILE_on_indentation(lexer* me, const int Indentation) {
assert(Indentation >= 0);
    }
#endif

#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    bool
    lexer__END_OF_FILE_has_base(const quex_mode* Mode) {
    return false;
    }
    bool
    lexer__END_OF_FILE_has_entry_from(const quex_mode* Mode) {
    return true; // default
    }
    bool
    lexer__END_OF_FILE_has_exit_to(const quex_mode* Mode) {
    return true; // default
    }
#endif    

    void
    lexer__STRING_READER_on_entry(lexer* me, const quex_mode* FromMode) {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->STRING_READER.has_entry_from(FromMode));
#endif

#line 145 "simple.qx"
 self.accumulator.clear(); 
#line 62 "lexer.cpp"
    }
    void
    lexer__STRING_READER_on_exit(lexer* me, const quex_mode* ToMode)  {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->STRING_READER.has_exit_to(ToMode));
#endif

#line 149 "simple.qx"
 
	self.accumulator.flush(TKN_STRING); 
	self.send(TKN_QUOTE);
    
#line 75 "lexer.cpp"

    }

#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT        
    void
    lexer__STRING_READER_on_indentation(lexer* me, const int Indentation) {
assert(Indentation >= 0);
    }
#endif

#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    bool
    lexer__STRING_READER_has_base(const quex_mode* Mode) {

    switch( Mode->id ) {
    case LEX_ID_END_OF_FILE: return true;
    default:
    ;
    }
    #ifdef __QUEX_OPTION_ERROR_OUTPUT_ON_MODE_CHANGE_ERROR
    std::cerr << "mode 'END_OF_FILE' is not one of:\n";    std::cerr << "         END_OF_FILE\n";
    #endif // QUEX_OPTION_ERROR_OUTPUT_ON_MODE_CHANGE_ERROR
    return false;
    
    }
    bool
    lexer__STRING_READER_has_entry_from(const quex_mode* Mode) {
    return true; // default
    }
    bool
    lexer__STRING_READER_has_exit_to(const quex_mode* Mode) {
    return true; // default
    }
#endif    

    void
    lexer__PROGRAM_on_entry(lexer* me, const quex_mode* FromMode) {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->PROGRAM.has_entry_from(FromMode));
#endif

    }
    void
    lexer__PROGRAM_on_exit(lexer* me, const quex_mode* ToMode)  {
#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
assert(me->PROGRAM.has_exit_to(ToMode));
#endif

    }

#ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT        
    void
    lexer__PROGRAM_on_indentation(lexer* me, const int Indentation) {
assert(Indentation >= 0);
    }
#endif

#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    bool
    lexer__PROGRAM_has_base(const quex_mode* Mode) {

    switch( Mode->id ) {
    case LEX_ID_END_OF_FILE: return true;
    default:
    ;
    }
    #ifdef __QUEX_OPTION_ERROR_OUTPUT_ON_MODE_CHANGE_ERROR
    std::cerr << "mode 'END_OF_FILE' is not one of:\n";    std::cerr << "         END_OF_FILE\n";
    #endif // QUEX_OPTION_ERROR_OUTPUT_ON_MODE_CHANGE_ERROR
    return false;
    
    }
    bool
    lexer__PROGRAM_has_entry_from(const quex_mode* Mode) {
    return true; // default
    }
    bool
    lexer__PROGRAM_has_exit_to(const quex_mode* Mode) {
    return true; // default
    }
#endif    
#undef self
} // END: namespace quex
