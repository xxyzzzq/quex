/* -*- C++ -*- vim:set syntax=cpp:
 *
 * No include guards, the header might be included from multiple lexers.
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_MODE_HANDLING_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_MODE_HANDLING_I__  */

#ifndef __QUEX_SETTING_PLAIN_C
namespace quex { 
#endif

    QUEX_INLINE QUEX_TYPE_MODE&
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, mode)() 
    { return *__current_mode_p; }

    QUEX_INLINE int
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, mode_id)() const
    { return __current_mode_p->id; }

    QUEX_INLINE const char*
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, mode_name)() const
    { return __current_mode_p->name; }

#   ifdef QUEX_OPTION_DEBUG_MODE_TRANSITIONS
    QUEX_INLINE void
    QUEX_DEBUG_PRINT_TRANSITION(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_MODE* Source, QUEX_TYPE_MODE* Target)
    {
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        std::cout << "line = " << me->line_number_at_begin() << std::endl;
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        std::cout << "column = " << me->column_number_at_begin() << std::endl;
#       endif
        if( Source != 0x0 ) std::cout << "FromMode: " << Source->name << " ";
        std::cout << "ToMode: " << Target->name << std::endl;
    }
#else 
#   define QUEX_DEBUG_PRINT_TRANSITION(ME, X, Y) /* empty */
#   endif

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, set_mode_brutally)(const int ModeID)
    { set_mode_brutally(*(mode_db[ModeID])); }

    QUEX_INLINE void 
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, set_mode_brutally)(const QUEX_TYPE_MODE& Mode) 
    { 
        /* To be optimized aways if its function body is empty (see above) */
        QUEX_DEBUG_PRINT_TRANSITION(this, __current_mode_p, (QUEX_TYPE_MODE*)&Mode);  

        __current_mode_p                        = (QUEX_TYPE_MODE*)&Mode;
        QuexAnalyser::current_analyser_function = Mode.analyser_function; 
    }

    QUEX_INLINE void    
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, enter_mode)(/* NOT const*/ QUEX_TYPE_MODE& TargetMode) 
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
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, operator)<<(const int ModeID) 
    { enter_mode(map_mode_id_to_mode(ModeID)); }

    QUEX_INLINE void 
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, operator)<<(/* NOT const*/ QUEX_TYPE_MODE& Mode) 
    { enter_mode(Mode); }


    QUEX_INLINE void 
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, pop_mode)() 
    { 
        __quex_assert(_mode_stack.end != _mode_stack.begin);
        --_mode_stack.end;
        enter_mode(**_mode_stack.end); 
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, pop_drop_mode)() 
    { 
        __quex_assert(_mode_stack.end != _mode_stack.begin);
        --_mode_stack.end;
        // do not care about what was popped
    }
        
    QUEX_INLINE void       
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, push_mode)(QUEX_TYPE_MODE& new_mode) 
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
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, map_mode_id_to_mode)(const int ModeID)
    { 
        __quex_assert(ModeID >= 0);
        __quex_assert(ModeID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1); // first mode is unused by quex
        return *(mode_db[ModeID]); 
    }

    QUEX_INLINE int  
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, map_mode_to_mode_id)(const QUEX_TYPE_MODE& Mode) const
    { return Mode.id; }

#ifndef __QUEX_SETTING_PLAIN_C
} /* namespace quex { */
#endif

