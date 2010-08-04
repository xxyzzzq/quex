/* (C) 2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY       */
#ifndef __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I
#define __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I

    QUEX_INLINE void      
    QUEX_NAME(IndentationHandler_init)(QUEX_NAME(IndentationHandler)* me)
    {
        me->end        = me->begin;
        me->memory_end = me->begin + QUEX_SETTING_INDENTATION_STACK_SIZE;

        /* first indentation at column = 0 */
        IndentationHandler_push(0);
        /* Default: Do not allow to open a sub-block. Constructs like 'for' loops
         * 'if' blocks etc. should allow the opening of an indentation.           */
        me->allow_opening_indentation_f = false;
    }

    QUEX_INLINE void      
    QUEX_NAME(IndentationHandler_on_indentation)(QUEX_TYPE_ANALYZER*  lexer, 
                                               const size_t         Indentation)
    {
        QUEX_NAME(IndentationHandler)*    me = lexer->indentation_stack;

        /* There should be at least the '0' indentation in place, thus: */
        __quex_assert(me->end > me->begin);

        if( Indentation > *(me->end - 1) ) {
            if( me->_enabled_f ) {
                self_send(QUEX_TKN_BLOCK_OPEN);
                IndentationHandler_push(&self.indentation_stack, (uint16_t)Indentation);
                me->_enabled_f = false;
            }
            else {
                /* -- higher indentation where it was not allowed to indent higher
                 *    => misaligned indentation                                    */
                self_token_p()->number = (int)self_line_number(); 
                self_send(__QUEX_SETTING_TOKEN_ID_INDENTATION_ERROR);
            }
            return;
        }
        while( *(me->end - 1) > Indentation ) {
            self_send(QUEX_TKN_BLOCK_CLOSE);     
            IndentationHandler_pop(&self.indentation_stack);
        }

        /* -- 'landing' indentation has to fit an indentation border
         *    if not send an error.                                  */
        if( *(me->end - 1) != Indentation ) {
            self_token_p()->number = (int)self_line_number(); 
            self_send(__QUEX_SETTING_TOKEN_ID_INDENTATION_ERROR);
        }
    }

    void
    QUEX_NAME(IndentationHandler_push)(QUEX_NAME(IndentationHandler)* me, uint16_t Indentation)
    {
        if( me->end == me->memory_end ) QUEX_ERROR_EXIT("Indentation stack overflow.");
        *(me->end++) = Indentation;
    }

    uint16_t
    QUEX_NAME(IndentationHandler_pop)(QUEX_NAME(IndentationHandler)* me)
    {
        __quex_assert( me->end != me->begin );
        return *(--(me->end));
    }

    void      
    QUEX_NAME(IndentationHandler_enable)(QUEX_NAME(IndentationHandler)* me)
    { me->_enabled_f = true; } 
    
    void
    QUEX_NAME(IndentationHandler_disable)(QUEX_NAME(IndentationHandler)* me)
    { me->_enabled_f = false; } 


#endif /* __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I */
