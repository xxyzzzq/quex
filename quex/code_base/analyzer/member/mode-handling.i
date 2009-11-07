/* -*- C++ -*- vim:set syntax=cpp:
 *
 * No include guards, the header might be included from multiple lexers.
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_MODE_HANDLING_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_MODE_HANDLING_I__  */
#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/Mode>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE QUEX_NAME(Mode)*
    QUEX_NAME(Analyzer_get_mode)() 
    { return me->engine.__current_mode_p; }

    QUEX_INLINE int
    QUEX_NAME(Analyzer_get_mode_id)() const
    { return me->engine.__current_mode_p->id; }

    QUEX_INLINE const char*
    QUEX_NAME(Analyzer_get_mode_name)() const
    { return me->engine.__current_mode_p->name; }

    QUEX_INLINE void
    QUEX_NAME(Analyzer_set_mode_brutally_by_id)(const int ModeID)
    { QUEX_NAME(Analyzer_set_mode_brutally)(*(me->mode_db[ModeID])); }

    QUEX_INLINE void 
    QUEX_NAME(Analyzer_set_mode_brutally)(const QUEX_NAME(Mode)* ModeP) 
    { 
#   ifdef     QUEX_OPTION_DEBUG_MODE_TRANSITIONS
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        __QUEX_STD_printf("line = %i\n", (int)me->line_number_at_begin());
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __QUEX_STD_printf("column = %i\n", (int)me->column_number_at_begin();
#       endif
        if( me->engine.__current_mode_p != 0x0 ) 
            __QUEX_STD_printf("FromMode: %s ", me->engine.__current_mode_p->name);
        __QUEX_STD_printf("ToMode: %s\n", Mode.name);
#    endif

        me->engine.__current_mode_p          = ModeP;
        me->engine.current_analyzer_function = ModeP->analyzer_function; 
    }

    QUEX_INLINE void    
    QUEX_NAME(Analyzer_enter_mode)(/* NOT const*/ QUEX_NAME(Mode)* TargetMode) 
    {
#       ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
        /* NOT const */ QUEX_NAME(Mode)* SourceMode = me->engine.__current_mode_p;
#       endif
#       ifdef __QUEX_OPTION_ON_EXIT_HANDLER_PRESENT
        SourceMode.on_exit(this, SourceMode);
#       endif
        QUEX_NAME(Analyzer_set_mode_brutally)(TargetMode);
#       ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
        TargetMode.on_entry(this, TargetMode);         
#       endif
    }

    QUEX_INLINE QUEX_NAME(Mode)*
    QUEX_NAME(Analyzer_map_mode_id_to_mode)(const int ModeID)
    { 
        __quex_assert(ModeID >= 0);
        __quex_assert(ModeID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1); // first mode is unused by quex
        return me->mode_db[ModeID]; 
    }

    QUEX_INLINE int  
    QUEX_NAME(Analyzer_map_mode_to_mode_id)(const QUEX_NAME(Mode)* Mode) const
    { return Mode->id; }

    QUEX_INLINE void 
    QUEX_NAME(Analyzer_pop_mode)() 
    { 
        __quex_assert(_mode_stack.end != _mode_stack.begin);
        --_mode_stack.end;
        enter_mode(**_mode_stack.end); 
    }

    QUEX_INLINE void
    QUEX_NAME(Analyzer_pop_drop_mode)() 
    { 
        __quex_assert(_mode_stack.end != _mode_stack.begin);
        --_mode_stack.end;
        // do not care about what was popped
    }
        
    QUEX_INLINE void       
    QUEX_NAME(Analyzer_push_mode)(QUEX_NAME(Mode)& new_mode) 
    { 
#       ifdef QUEX_OPTION_ASSERTS
        if( _mode_stack.end == _mode_stack.memory_end ) 
            QUEX_ERROR_EXIT("Mode stack overflow. Adapt size of mode stack via the macro "
                            "QUEX_SETTING_MODE_STACK_SIZE, or review mode transitions. "
                            "I.e. check that for every GOSUB (push), there is a correspondent "
                            "GOUP (pop).");
#       endif
        *_mode_stack.end = me->engine.__current_mode_p;
        ++_mode_stack.end;
        enter_mode(new_mode); 
    }

#   ifndef __QUEX_SETTING_PLAIN_C
    QUEX_INLINE QUEX_NAME(Mode)&
    QUEX_TYPE_ANALYZER::mode()
    { return *QUEX_NAME(Analyzer_get_mode)(); }
    
    QUEX_TYPE_ANALYZER::mode_id()
    { return QUEX_NAME(Analyzer_get_mode_id)(); }
    
    QUEX_INLINE const char*
    QUEX_TYPE_ANALYZER::get_mode_name)() const
    { return QUEX_NAME(Analyzer_get_mode_name)(); }

    QUEX_INLINE void
    QUEX_TYPE_ANALYZER::Analyzer_set_mode_brutally(const int ModeID)
    { QUEX_NAME(Analyzer_set_mode_brutally_by_id)(ModeID); }

    QUEX_INLINE void 
    QUEX_TYPE_ANALYZER::set_mode_brutally(const QUEX_NAME(Mode)& Mode) 
    { QUEX_NAME(Analyzer_set_mode_brutally)(&Mode); }

    QUEX_INLINE void    
    QUEX_TYPE_ANALYZER::enter_mode(/* NOT const*/ QUEX_NAME(Mode)& TargetMode) 
    { QUEX_NAME(Analyzer_enter_mode)(&TargetMode); }

    QUEX_INLINE QUEX_NAME(Mode)&
    QUEX_TYPE_ANALYZER::map_mode_id_to_mode(const int ModeID)
    { QUEX_NAME(Analyzer_map_mode_id_to_mode)(ModeID); }

    QUEX_INLINE int  
    QUEX_TYPE_ANALYZER::map_mode_to_mode_id(const QUEX_NAME(Mode)& Mode) const
    { QUEX_NAME(Analyzer_map_mode_to_mode_id)(const QUEX_NAME(Mode)* Mode); }

    QUEX_INLINE void 
    QUEX_TYPE_ANALYZER::operator<<(const int ModeID) 
    { QUEX_NAME(Analyzer_enter_mode)(map_mode_id_to_mode(ModeID)); }

    QUEX_INLINE void 
    QUEX_TYPE_ANALYZER::operator<<(/* NOT const*/ QUEX_NAME(Mode)* Mode) 
    { QUEX_NAME(Analyzer_enter_mode)(&Mode); }

    QUEX_INLINE void 
    QUEX_TYPE_ANALYZER::pop_mode() 
    { QUEX_NAME(Analyzer_pop_mode)(); }

    QUEX_INLINE void
    QUEX_TYPE_ANALYZER::pop_drop_mode() 
    { QUEX_NAME(Analyzer_pop_drop_mode)(); }

    QUEX_INLINE void       
    QUEX_TYPE_ANALYZER::push_mode(QUEX_NAME(Mode)& new_mode) 
    { QUEX_NAME(Analyzer_push_mode)(QUEX_NAME(Mode)& new_mode); }

#   endif

QUEX_NAMESPACE_MAIN_CLOSE

