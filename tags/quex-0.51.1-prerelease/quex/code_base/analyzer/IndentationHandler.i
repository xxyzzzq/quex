/* (C) 2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY       */
#ifndef __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I
#define __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I

    void      
    QUEX_NAME(IndentationStack_enable)(QUEX_NAME(IndentationStack)* me)
    { me->_enabled_f = true; } 
    
    void
    QUEX_NAME(IndentationHandler_disable)(QUEX_NAME(IndentationHandler)* me)
    { me->_enabled_f = false; } 


#endif /* __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I */
