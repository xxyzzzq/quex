// -*- C++ -*- vim:set syntax=cpp:
namespace quex { 
inline QuexMode&
CLASS::mode() 
{ return *__current_mode_p; }

inline int
CLASS::mode_id() const
{ return __current_mode_p->id; }

inline const char*
CLASS::mode_name() const
{ return __current_mode_p->name; }

#   ifdef QUEX_OPTION_DEBUG_MODE_TRANSITIONS
inline void
QUEX_DEBUG_PRINT_TRANSITION(CLASS* me, QuexMode* Source, QuexMode* Target)
{
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    std::cerr << "line = " << me->line_number_at_begin() << std::endl;
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    std::cerr << "column = " << me->column_number_at_begin() << std::endl;
#       endif
    if( Source != 0x0 ) std::cerr << "FromMode: " << Source->name;
    std::cerr << " ToMode: " << Target->name << std::endl;
}
#else 
#   define QUEX_DEBUG_PRINT_TRANSITION(ME, X, Y) /* empty */
#   endif

inline void
CLASS::set_mode_brutally(const int ModeID)
{ set_mode_brutally(*(mode_db[ModeID])); }

inline void 
CLASS::set_mode_brutally(const QuexMode& Mode) 
{ 
    /* To be optimized aways if its function body is empty (see above) */
    QUEX_DEBUG_PRINT_TRANSITION(this, __current_mode_p, (QuexMode*)&Mode);  

    __current_mode_p                        = (QuexMode*)&Mode;
    QuexAnalyser::current_analyser_function = Mode.analyser_function; 
}

inline void    
CLASS::enter_mode(/* NOT const*/ QuexMode& TargetMode) 
{
#   ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
    /* NOT const */ QuexMode& SourceMode = mode();
#   endif

#   ifdef __QUEX_OPTION_ON_EXIT_HANDLER_PRESENT
    SourceMode.on_exit(this, &TargetMode);
#   endif

    set_mode_brutally(TargetMode.id);

#   ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
    TargetMode.on_entry(this, &SourceMode);         
#   endif
}

inline void 
CLASS::operator<<(const int ModeID) 
{ enter_mode(map_mode_id_to_mode(ModeID)); }

inline void 
CLASS::operator<<(/* NOT const*/ QuexMode& Mode) 
{ enter_mode(Mode); }


inline void 
CLASS::pop_mode() 
{ 
    __quex_assert(_mode_stack.size() != 0);
    QuexMode* tmp; 
    tmp = _mode_stack.back(); 
    _mode_stack.pop_back(); 
    enter_mode(*tmp); 
}

inline void
CLASS::pop_drop_mode() 
{ 
    __quex_assert(_mode_stack.size() != 0);
    _mode_stack.pop_back(); // do not care about what was popped
}
    
inline void       
CLASS::push_mode(QuexMode& new_mode) 
{ 
    _mode_stack.push_back(&(mode())); 
    enter_mode(new_mode); 
}


inline QuexMode&
CLASS::map_mode_id_to_mode(const int ModeID)
{ 
    __quex_assert(ModeID >= 0);
    __quex_assert(ModeID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1); // first mode is unused by quex
    return *(mode_db[ModeID]); 
}

inline int  
CLASS::map_mode_to_mode_id(const QuexMode& Mode) const
{ return Mode.id; }
}
