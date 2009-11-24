/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2004-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_NAME(Accumulator) must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I

#ifndef   QUEX_TYPE_ANALYZER
#   error "Macro QUEX_TYPE_ANALYZER must be defined before inclusion of this file."
#endif


#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

    TEMPLATE_IN(InputHandleT) void    
    QUEX_FUNC(include_push)(QUEX_TYPE_ANALYZER*   me,
                            QUEX_TYPE_CHARACTER*  InputName,
                            const int             MODE_ID /* = -1 */, 
                            const char*           IANA_CodingName /* = 0x0 */)
    {
#       if defined(__QUEX_SETTING_PLAIN_C)
#       define InputHandleT  FILE
#       endif
        /* Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]             */
        __quex_assert(    MODE_ID == -1 
                      || (MODE_ID >= 1 && MODE_ID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1));
        /* IANA_CodingName == 0x0 possible if normal ASCII is ment (e.g. no iconv support) */

        /* Store the lexical analyzer's to the state before the including */
        /* Here, the 'memento_pack' section is executed                   */
        InputHandleT*        input_handle = 0x0;
        QUEX_NAME(Memento)*  m            = QUEX_FUNC(memento_pack)<InputHandleT>(me, InputName, &input_handle);
        if( m == 0x0 ) return;
        if( input_handle == 0x0 ) {
            QUEX_ERROR_EXIT("Segment 'memento_pack' segment did not set the input_handle.");
        }

        /* Initialize the lexical analyzer for the new input stream.             */
        /* Include stacks cannot be used with plain direct user memory => 0x0, 0 */
        QUEX_NAME(AnalyzerData_construct)((QUEX_NAME(AnalyzerData)*)me, input_handle,
                                          0x0, QUEX_SETTING_BUFFER_SIZE,
                                          IANA_CodingName, 
                                          QUEX_SETTING_TRANSLATION_BUFFER_SIZE,
                                          me->buffer._byte_order_reversion_active_f);

        if( MODE_ID != -1 ) QUEX_FUNC(set_mode_brutally_by_id)(me, MODE_ID);

#       ifdef __QUEX_OPTION_COUNTER
        QUEX_FIX(COUNTER, _reset)(&me->counter);
#       endif

        /* Keep track of 'who's your daddy?'                              */
        me->_parent_memento = m;
#       if defined(__QUEX_SETTING_PLAIN_C)
#       undef InputHandleT
#       endif
    }   

    TEMPLATE_IN(InputHandleT) void    
    QUEX_FUNC(include_push_mode)(QUEX_TYPE_ANALYZER*      me,
                                 QUEX_TYPE_CHARACTER*     InputName,
                                 const QUEX_NAME(Mode)*   mode, 
                                 const char*              IANA_CodingName /* = 0x0 */)
    {
        /* Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N] */
#       ifndef __QUEX_SETTING_PLAIN_C
        QUEX_FUNC(include_push)<InputHandleT>((QUEX_NAME(AnalyzerData)*)me, InputName, mode->id(), IANA_CodingName);
#       else
        QUEX_FUNC(include_push)((QUEX_NAME(AnalyzerData)*)me, InputName, mode->id(), IANA_CodingName);
#       endif
    }


    QUEX_INLINE bool
    QUEX_FUNC(include_pop)(QUEX_TYPE_ANALYZER* me) 
    {
        /* Not included? return 'false' to indicate we're on the top level     */
        if( me->_parent_memento == 0x0 ) return false; 

        /* Free the related memory that is no longer used                      */
        QUEX_NAME(AnalyzerData_destruct)(me);

        /* Restore the lexical analyzer to the state it was before the include */
        /* Here, the 'memento_unpack' section is executed                      */
        QUEX_FUNC(memento_unpack)(me, me->_parent_memento);

        /* Return to including file succesful */
        return true;
    }

    QUEX_INLINE void
    QUEX_FUNC(include_stack_delete)(QUEX_TYPE_ANALYZER* me) 
    {
        while( me->_parent_memento != 0x0 ) {
            /* Free the related memory that is no longer used                      */
            QUEX_NAME(AnalyzerData_destruct)(me);

            /* Restore the lexical analyzer to the state it was before the include */
            /* Here, the 'memento_unpack' section is executed                      */
            QUEX_FUNC(memento_unpack)(me, me->_parent_memento);
        }
    }

#if ! defined( __QUEX_SETTING_PLAIN_C )
    TEMPLATE_IN(InputHandleT) void    
    QUEX_MEMBER(include_push)(QUEX_TYPE_CHARACTER*   InputName,
                              const int              ModeID /* = -1 */, 
                              const char*            IANA_CodingName /* = 0x0 */)
    { QUEX_FUNC(include_push)<InputHandleT>(this, InputName, ModeID, IANA_CodingName); }

    TEMPLATE_IN(InputHandleT) void    
    QUEX_MEMBER(include_push)(QUEX_TYPE_CHARACTER*     InputName,
                              const QUEX_NAME(Mode)&   mode, 
                              const char*              IANA_CodingName /* = 0x0 */)
    { QUEX_FUNC(include_push_mode)<InputHandleT>(this, InputName, mode, IANA_CodingName); }

    QUEX_INLINE bool
    QUEX_MEMBER(include_pop)() 
    { return QUEX_FUNC(include_pop)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(include_stack_delete)() 
    { QUEX_FUNC(include_stack_delete)(this); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I */
