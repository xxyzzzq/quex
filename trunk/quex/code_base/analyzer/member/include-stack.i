/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2004-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_TYPE_ACCUMULATOR must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I

#ifndef   QUEX_TYPE_ANALYZER
#   error "Macro QUEX_TYPE_ANALYZER must be defined before inclusion of this file."
#endif

#include <quex/code_base/analyzer/Engine>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_COMPONENTS_OPEN

    TEMPLATE_IN(InputHandleT) void    
    QUEX_MEMFUNC(ANALYZER, include_push)(__QUEX_SETTING_THIS_POINTER
                                         QUEX_TYPE_CHARACTER*    InputName,
                                         const QUEX_TYPE_MODE&   mode, 
                                         const char*             IANA_CodingName /* = 0x0 */)
    {
        /* Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N] */
#       ifndef __QUEX_SETTING_PLAIN_C
        include_push<InputHandleT>(InputName, mode.id(), IANA_CodingName);
#       else
        QUEX_MEMFUNC(ANALYZER, include_push)(InputName, mode.id(), IANA_CodingName);
#       endif
    }

    TEMPLATE_IN(InputHandleT) void    
    QUEX_MEMFUNC(ANALYZER, include_push)(__QUEX_SETTING_THIS_POINTER
                                         QUEX_TYPE_CHARACTER*     InputName,
                                         const int                MODE_ID /* = -1 */, 
                                         const char*              IANA_CodingName /* = 0x0 */)
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
        InputHandleT*       input_handle = 0x0;
        QUEX_TYPE_MEMENTO*  m            = QUEX_FIX(ANALYZER, _memento_pack)<InputHandleT>(this, InputName, &input_handle);
        if( m == 0x0 ) return;
        if( input_handle == 0x0 ) {
            QUEX_ERROR_EXIT("Segment 'memento_pack' segment did not set the input_handle.");
        }

        if( MODE_ID != -1 ) this->set_mode_brutally(MODE_ID);

        /* Initialize the lexical analyzer for the new input stream.             */
        /* Include stacks cannot be used with plain direct user memory => 0x0, 0 */
        QuexAnalyzerEngine_construct(&this->engine,
                                     engine.__current_mode_p->analyzer_function,
                                     input_handle,
                                     0x0, QUEX_SETTING_BUFFER_SIZE,
                                     IANA_CodingName, 
                                     QUEX_SETTING_TRANSLATION_BUFFER_SIZE,
                                     engine.buffer._byte_order_reversion_active_f);

#       ifdef __QUEX_OPTION_COUNTER
        QUEX_FIX(COUNTER, _reset)(&counter);
#       endif

        /* Keep track of 'who's your daddy?'                              */
        m->base.parent = this->_parent_memento;
        this->_parent_memento = m;
#       if defined(__QUEX_SETTING_PLAIN_C)
#       undef InputHandleT
#       endif
    }   

    QUEX_INLINE bool
    QUEX_MEMFUNC(ANALYZER, include_pop)(__QUEX_SETTING_THIS_POINTER) 
    {
        /* Not included? return 'false' to indicate we're on the top level     */
        if( this->_parent_memento == 0x0 ) return false; 

        /* Free the related memory that is no longer used                      */
        QuexAnalyzerEngine_destruct(&this->engine);

        /* Restore the lexical analyzer to the state it was before the include */
        /* Here, the 'memento_unpack' section is executed                      */
        QUEX_FIX(ANALYZER, _memento_unpack)(this, this->_parent_memento);

        /* Return to including file succesful */
        return true;
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(ANALYZER, include_stack_delete)(__QUEX_SETTING_THIS_POINTER) 
    {
        while( this->_parent_memento != 0x0 ) {
            /* Free the related memory that is no longer used                      */
            QuexAnalyzerEngine_destruct(&this->engine);

            /* Restore the lexical analyzer to the state it was before the include */
            /* Here, the 'memento_unpack' section is executed                      */
            QUEX_FIX(ANALYZER, _memento_unpack)(this, this->_parent_memento);
        }
    }

QUEX_NAMESPACE_COMPONENTS_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I */
