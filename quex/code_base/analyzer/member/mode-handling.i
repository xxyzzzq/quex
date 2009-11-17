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
    QUEX_FUNC(get_mode)(QUEX_NAME(AnalyzerData)* me) 
    { return me->__current_mode_p; }

    QUEX_INLINE int
    QUEX_FUNC(get_mode_id)(const QUEX_NAME(AnalyzerData)* me)
    { return me->__current_mode_p->id; }

    QUEX_INLINE const char*
    QUEX_FUNC(get_mode_name)(const QUEX_NAME(AnalyzerData)* me)
    { return me->__current_mode_p->name; }

    QUEX_INLINE void 
    QUEX_FUNC(set_mode_brutally)(QUEX_NAME(AnalyzerData)* me, QUEX_NAME(Mode)* ModeP) 
    { 
#   ifdef     QUEX_OPTION_DEBUG_MODE_TRANSITIONS
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        __QUEX_STD_printf("line = %i\n", (int)me->line_number_at_begin());
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __QUEX_STD_printf("column = %i\n", (int)me->column_number_at_begin();
#       endif
        if( me->__current_mode_p != 0x0 ) 
            __QUEX_STD_printf("FromMode: %s ", me->__current_mode_p->name);
        __QUEX_STD_printf("ToMode: %s\n", Mode.name);
#    endif

        me->__current_mode_p          = ModeP;
        me->current_analyzer_function = ModeP->analyzer_function; 
    }

    QUEX_INLINE void
    QUEX_FUNC(set_mode_brutally_by_id)(QUEX_NAME(AnalyzerData)* me, const int ModeID)
    { QUEX_FUNC(set_mode_brutally)(me, me->mode_db[ModeID]); }

    QUEX_INLINE void    
    QUEX_FUNC(enter_mode)(QUEX_NAME(AnalyzerData)* me, /* NOT const*/ QUEX_NAME(Mode)* TargetMode) 
    {
#       ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
        /* NOT const */ QUEX_NAME(Mode)* SourceMode = me->__current_mode_p;
#       endif
#       ifdef __QUEX_OPTION_ON_EXIT_HANDLER_PRESENT
        SourceMode->on_exit(me, SourceMode);
#       endif
        QUEX_FUNC(set_mode_brutally)(me, TargetMode);
#       ifdef __QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT
        TargetMode->on_entry(me, TargetMode);         
#       endif
    }

    QUEX_INLINE QUEX_NAME(Mode)*
    QUEX_FUNC(map_mode_id_to_mode)(QUEX_NAME(AnalyzerData)* me, const int ModeID)
    { 
        __quex_assert(ModeID >= 0);
        __quex_assert(ModeID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1); // first mode is unused by quex
        return me->mode_db[ModeID]; 
    }

    QUEX_INLINE int  
    QUEX_FUNC(map_mode_to_mode_id)(const QUEX_NAME(AnalyzerData)* me, const QUEX_NAME(Mode)* Mode)
    { return Mode->id; }

    QUEX_INLINE void 
    QUEX_FUNC(pop_mode)(QUEX_NAME(AnalyzerData)* me) 
    { 
        __quex_assert(me->_mode_stack.end != me->_mode_stack.begin);
        --(me->_mode_stack.end);
        QUEX_FUNC(enter_mode)(me, *me->_mode_stack.end); 
    }

    QUEX_INLINE void
    QUEX_FUNC(pop_drop_mode)(QUEX_NAME(AnalyzerData)* me) 
    { 
        __quex_assert(me->_mode_stack.end != me->_mode_stack.begin);
        --(me->_mode_stack.end);
        // do not care about what was popped
    }
        
    QUEX_INLINE void       
    QUEX_FUNC(push_mode)(QUEX_NAME(AnalyzerData)* me, QUEX_NAME(Mode)* new_mode) 
    { 
#       ifdef QUEX_OPTION_ASSERTS
        if( me->_mode_stack.end == me->_mode_stack.memory_end ) 
            QUEX_ERROR_EXIT("Mode stack overflow. Adapt size of mode stack via the macro "
                            "QUEX_SETTING_MODE_STACK_SIZE, or review mode transitions. "
                            "I.e. check that for every GOSUB (push), there is a correspondent "
                            "GOUP (pop).");
#       endif
        *me->_mode_stack.end = me->__current_mode_p;
        ++(me->_mode_stack.end);
        QUEX_FUNC(enter_mode)(me, new_mode); 
    }

#   ifndef __QUEX_SETTING_PLAIN_C
    QUEX_INLINE QUEX_NAME(Mode)&
    QUEX_MEMBER(mode)()
    { return *QUEX_FUNC(get_mode)(this); }
    
    QUEX_INLINE int
    QUEX_MEMBER(mode_id)() const
    { return QUEX_FUNC(get_mode_id)(this); }
    
    QUEX_INLINE const char*
    QUEX_MEMBER(mode_name)() const
    { return QUEX_FUNC(get_mode_name)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(set_mode_brutally)(const int ModeID)
    { QUEX_FUNC(set_mode_brutally_by_id)(this, ModeID); }

    QUEX_INLINE void 
    QUEX_MEMBER(set_mode_brutally)(const QUEX_NAME(Mode)& TheMode) 
    { QUEX_FUNC(set_mode_brutally)(this, ((QUEX_NAME(Mode)*)&TheMode)); }

    QUEX_INLINE void    
    QUEX_MEMBER(enter_mode)(/* NOT const*/ QUEX_NAME(Mode)& TargetMode) 
    { QUEX_FUNC(enter_mode)(this, &TargetMode); }

    QUEX_INLINE QUEX_NAME(Mode)&
    QUEX_MEMBER(map_mode_id_to_mode)(const int ModeID)
    { return *(QUEX_FUNC(map_mode_id_to_mode)(this, ModeID)); }

    QUEX_INLINE int  
    QUEX_MEMBER(map_mode_to_mode_id)(const QUEX_NAME(Mode)& TheMode) const
    { return QUEX_FUNC(map_mode_to_mode_id)(this, &TheMode); }

    QUEX_INLINE void 
    QUEX_MEMBER(operator)<<(const int ModeID) 
    { enter_mode(*(QUEX_FUNC(map_mode_id_to_mode)(this, ModeID))); }

    QUEX_INLINE void 
    QUEX_MEMBER(operator)<<(/* NOT const*/ QUEX_NAME(Mode)& TheMode) 
    { enter_mode(TheMode); }

    QUEX_INLINE void 
    QUEX_MEMBER(pop_mode)() 
    { QUEX_FUNC(pop_mode)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(pop_drop_mode)() 
    { QUEX_FUNC(pop_drop_mode)(this); }

    QUEX_INLINE void       
    QUEX_MEMBER(push_mode)(QUEX_NAME(Mode)& new_mode) 
    { QUEX_FUNC(push_mode)(this, &new_mode); }

#   endif

QUEX_NAMESPACE_MAIN_CLOSE

