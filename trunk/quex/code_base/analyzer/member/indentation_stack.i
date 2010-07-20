#ifndef __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I
#define __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I

    QUEX_INLINE void      
    QUEX_NAME(IndentationStack_init)(IndentationStack* me)
    {
        me->end        = me->begin;
        me->memory_end = me->begin + QUEX_SETTING_INDENTATION_STACK_SIZE;

        /* first indentation at column = 0 */
        IndentationStack_push(0);
        /* Default: do not allow to open a sub-block.
         * only function definitions, if statements, and for loops
         * shoul allow to open a new indentation block in the next line. */
        IndentationStack_sleep();
    }

    QUEX_INLINE void      
    QUEX_NAME(IndentationStack_on_indentation)(QUEX_TYPE_ANALYZER*  me, 
                                                         const size_t         Indentation)
    {
        /* There should be at least the '0' indentation in place, thus: */
        __quex_assert(me->end > me->begin);

        if( Indentation > *(me->end - 1) ) {
            if( self.allow_opening_indentation_f ) {
                self_send(QUEX_TKN_BLOCK_OPEN);
                IndentationStack_push(&self.indentation_stack, (uint16_t)Indentation);
                self.allow_opening_indentation_f = false;
            }
            else {
                /* -- higher indentation where it was not allowed to indent higher
                 *    => misaligned indentation                                    */
                self_token_p()->number = (int)self_line_number(); 
                self_send(QUEX_TKN_ERROR_MISALIGNED_INDENTATION);
            }
            return;
        }
        while( *(me->end - 1) > Indentation ) {
            self_send(QUEX_TKN_BLOCK_CLOSE);     
            IndentationStack_pop(&self.indentation_stack);
        }

        /* -- 'landing' indentation has to fit an indentation border
         *    if not send an error.                                  */
        if( *(me->end - 1) != Indentation ) {
            self_token_p()->number = (int)self_line_number(); 
            self_send(QUEX_TKN_ERROR_MISALIGNED_INDENTATION);
        }
    }

    void
    QUEX_NAME(IndentationStack_push)(IndentationStack* me, uint16_t Indentation)
    {
        if( me->end == me->memory_end ) QUEX_ERROR_EXIT("Indentation stack overflow.");
        *(me->end++) = Indentation;
    }

    uint16_t
    QUEX_NAME(IndentationStack_pop)(IndentationStack* me)
    {
        __quex_assert( me->end != me->begin );
        return *(--(me->end));
    }

#endif /* __INCLUDE_GUARD__QUEX__INDENTATION_STACK_I */
