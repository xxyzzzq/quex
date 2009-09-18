/* -*- C++ -*- vim:set syntax=cpp:
 *
 * No include guards, the header might be included from multiple lexers.
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_MODE_HANDLING_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_MODE_HANDLING_I__  */
#include <quex/code_base/definitions>

QUEX_NAMESPACE_COMPONENTS_OPEN

    QUEX_INLINE QUEX_TYPE_MODE&
    QUEX_MEMFUNC(ANALYZER, mode)() 
    { return *__current_mode_p; }

    QUEX_INLINE int
    QUEX_MEMFUNC(ANALYZER, mode_id)() const
    { return __current_mode_p->id; }

    QUEX_INLINE const char*
    QUEX_MEMFUNC(ANALYZER, mode_name)() const
    { return __current_mode_p->name; }

    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, set_mode_brutally)(const int ModeID)
    { set_mode_brutally(*(mode_db[ModeID])); }

    QUEX_INLINE void 
    QUEX_MEMFUNC(ANALYZER, set_mode_brutally)(const QUEX_TYPE_MODE& Mode) 
    { 
#   ifdef     QUEX_OPTION_DEBUG_MODE_TRANSITIONS
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        __QUEX_STD_printf("line = %i\n", (int)me->line_number_at_begin());
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __QUEX_STD_printf("column = %i\n", (int)me->column_number_at_begin();
#       endif
        if( __current_mode_p != 0x0 ) 
            __QUEX_STD_printf("FromMode: %s ", __current_mode_p->name);
        __QUEX_STD_printf("ToMode: %s\n", Mode.name);
#    endif

        __current_mode_p                        = (QUEX_TYPE_MODE*)&Mode;
        QuexAnalyser::current_analyser_function = Mode.analyser_function; 
    }

    QUEX_INLINE void    
    QUEX_MEMFUNC(ANALYZER, enter_mode)(/* NOT const*/ QUEX_TYPE_MODE& TargetMode) 
    {
#   ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
        /* NOT const */ QUEX_TYPE_MODE& SourceMode = mode();
#   endif

#   ifdef __QUEX_OPTION_ON_EXIT_HANDLER_PRESENT
        SourceMode.on_exit(this, &SourceMode);
#   endif

        set_mode_brutally(TargetMode.id);

#   ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
        TargetMode.on_entry(this, &TargetMode);         
#   endif
    }

    QUEX_INLINE void 
    QUEX_MEMFUNC(ANALYZER, operator)<<(const int ModeID) 
    { enter_mode(map_mode_id_to_mode(ModeID)); }

    QUEX_INLINE void 
    QUEX_MEMFUNC(ANALYZER, operator)<<(/* NOT const*/ QUEX_TYPE_MODE& Mode) 
    { enter_mode(Mode); }


    QUEX_INLINE void 
    QUEX_MEMFUNC(ANALYZER, pop_mode)() 
    { 
        __quex_assert(_mode_stack.end != _mode_stack.begin);
        --_mode_stack.end;
        enter_mode(**_mode_stack.end); 
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, pop_drop_mode)() 
    { 
        __quex_assert(_mode_stack.end != _mode_stack.begin);
        --_mode_stack.end;
        // do not care about what was popped
    }
        
    QUEX_INLINE void       
    QUEX_MEMFUNC(ANALYZER, push_mode)(QUEX_TYPE_MODE& new_mode) 
    { 
#       ifdef QUEX_OPTION_ASSERTS
        if( _mode_stack.end == _mode_stack.memory_end ) 
            QUEX_ERROR_EXIT("Mode stack overflow. Adapt size of mode stack via the macro "
                            "QUEX_SETTING_MODE_STACK_SIZE, or review mode transitions. "
                            "I.e. check that for every GOSUB (push), there is a correspondent "
                            "GOUP (pop).");
#       endif
        *_mode_stack.end = &(mode());
        ++_mode_stack.end;
        enter_mode(new_mode); 
    }


    QUEX_INLINE QUEX_TYPE_MODE&
    QUEX_MEMFUNC(ANALYZER, map_mode_id_to_mode)(const int ModeID)
    { 
        __quex_assert(ModeID >= 0);
        __quex_assert(ModeID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1); // first mode is unused by quex
        return *(mode_db[ModeID]); 
    }

    QUEX_INLINE int  
    QUEX_MEMFUNC(ANALYZER, map_mode_to_mode_id)(const QUEX_TYPE_MODE& Mode) const
    { return Mode.id; }

QUEX_NAMESPACE_COMPONENTS_CLOSE

