/* -*- C++ -*-   vim: set syntax=cpp:
 * (C) Frankt-Rene Schaefer
 * ABSOLUTELY NO WARRANTY               */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__MISC_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__MISC_I

#include <quex/code_base/analyzer/counter/Base>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void    
QUEX_NAME(move_forward)(QUEX_TYPE_ANALYZER* me, const size_t CharacterN)
{
    QUEX_NAME(Buffer_move_forward)(&me->buffer, CharacterN);
}

QUEX_INLINE void    
QUEX_NAME(move_backward)(QUEX_TYPE_ANALYZER* me, const size_t CharacterN)
{
    QUEX_NAME(Buffer_move_backward)(&me->buffer, CharacterN);
}


QUEX_INLINE size_t  
QUEX_NAME(tell)(QUEX_TYPE_ANALYZER* me)
{
    return QUEX_NAME(Buffer_tell)(&me->buffer);
}

QUEX_INLINE void    
QUEX_NAME(seek)(QUEX_TYPE_ANALYZER* me, const size_t CharacterIndex)
{
    QUEX_NAME(Buffer_seek)(&me->buffer, CharacterIndex);
}

QUEX_INLINE QUEX_TYPE_TOKEN*  
QUEX_NAME(token_p)(QUEX_TYPE_ANALYZER* me)
{
#   define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
    return __QUEX_CURRENT_TOKEN_P;
#   undef self
}

#ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
#   if defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
    QUEX_INLINE QUEX_TYPE_TOKEN*
    QUEX_NAME(token_p_switch)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_TOKEN** UsersToken)
    {
        QUEX_TYPE_TOKEN* prev_token_p = me->token;
        me->token = UsersToken;
        return prev_token_p;
    }
#   endif
#else
    QUEX_INLINE bool
    QUEX_NAME(token_queue_is_empty)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_NAME(TokenQueue_is_empty)(&me->_token_queue); 
    }

    QUEX_INLINE void
    QUEX_NAME(token_queue_remainder_get)(QUEX_TYPE_ANALYZER*  me,
                                         QUEX_TYPE_TOKEN**    begin, 
                                         QUEX_TYPE_TOKEN**    end)
    { QUEX_NAME(TokenQueue_remainder_get)(&me->_token_queue, begin, end); }

#   if defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
    QUEX_INLINE void
    QUEX_NAME(token_queue_memory_switch)(QUEX_TYPE_ANALYZER* me, 
                                         QUEX_TYPE_TOKEN**   memory, size_t* n)
    { 
        QUEX_TYPE_TOKEN*  prev_memory = 0x0;
        size_t            prev_n      = (size_t)-1;
        QUEX_NAME(TokenQueue_memory_get)(&me->_token_queue, &prev_memory, &prev_n); 
        QUEX_NAME(TokenQueue_init)(&this->_token_queue, *memory, *n); 
        *memory = prev_memory;
        *n      = prev_n;
    }
#   endif

#endif


QUEX_INLINE const char* 
QUEX_NAME(version)(QUEX_TYPE_ANALYZER* me)
{ 
    return          QUEX_STRING(QUEX_TYPE_ANALYZER)           \
           ": Version "         QUEX_SETTING_ANALYZER_VERSION \
           ". Date "            QUEX_SETTING_BUILD_DATE       \
           "Generated by Quex " QUEX_SETTING_VERSION ".";
}

QUEX_INLINE bool
QUEX_NAME(byte_order_reversion)(QUEX_TYPE_ANALYZER* me)
{ return me->buffer._byte_order_reversion_active_f; }

QUEX_INLINE void     
QUEX_NAME(byte_order_reversion_set)(QUEX_TYPE_ANALYZER* me, bool Value)
{ me->buffer._byte_order_reversion_active_f = Value; }


QUEX_INLINE void
QUEX_NAME(print_this)(QUEX_TYPE_ANALYZER* me)
{
    QUEX_NAME(Mode)** iterator = 0x0;

    __QUEX_STD_printf("   CurrentMode = %s;\n", 
                      me->__current_mode_p == 0x0 ? 
                         "0x0" 
                      : 
                         me->__current_mode_p->name);

    QUEX_NAME(Buffer_print_this)(&me->buffer);

#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    QUEX_NAME(Accumulator_print_this)(&me->accumulator);
#   endif

#   ifdef __QUEX_OPTION_COUNTER
    QUEX_TYPE_COUNTER_PRINT_THIS(&me->counter);
#   endif

#   ifdef QUEX_OPTION_POST_CATEGORIZER
    QUEX_NAME(PostCategorizer_print_this)(&me->post_categorizer);
#   endif
    __QUEX_STD_printf("   Mode Stack (%i/%i) = [", 
                      (int)(me->_mode_stack.end        - me->_mode_stack.begin),
                      (int)(me->_mode_stack.memory_end - me->_mode_stack.begin));
    for(iterator=me->_mode_stack.end-1; iterator >= me->_mode_stack.begin; --iterator)
        __QUEX_STD_printf("%s, ", (*iterator)->name);

    __QUEX_STD_printf("]\n");
    __QUEX_STD_printf("   ByteOrderInversion = %s;\n", 
                      QUEX_NAME(byte_order_reversion)(me) ? "true" : "false");
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void    
QUEX_MEMBER(move_forward)(const size_t CharacterN)
{ QUEX_NAME(move_forward)(this, CharacterN); }

QUEX_INLINE void    
QUEX_MEMBER(move_backward)(const size_t CharacterN)
{ QUEX_NAME(move_backward)(this, CharacterN); }

QUEX_INLINE size_t  
QUEX_MEMBER(tell)()
{ return QUEX_NAME(tell)(this); }

QUEX_INLINE void    
QUEX_MEMBER(seek)(const size_t CharacterIndex)
{ QUEX_NAME(seek)(this, CharacterIndex); }

QUEX_INLINE QUEX_TYPE_TOKEN*  
QUEX_MEMBER(token_p)()
{ return QUEX_NAME(token_p)(this); }

#if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)

#   if defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
    QUEX_INLINE QUEX_TYPE_TOKEN*
    QUEX_MEMBER(token_p_switch)(QUEX_TYPE_TOKEN* TokenP)
    { return QUEX_NAME(token_p_switch)(this, TokenP); }
#   endif

#else
    QUEX_INLINE bool
    QUEX_MEMBER(token_queue_is_empty)()
    { return QUEX_NAME(token_queue_is_empty)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(token_queue_remainder_get)(QUEX_TYPE_TOKEN**  begin, 
                                           QUEX_TYPE_TOKEN**  end)
    { QUEX_NAME(token_queue_remainder_get)(this, begin, end); }

#   if defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
    QUEX_INLINE void
    QUEX_MEMBER(token_queue_memory_switch)(QUEX_TYPE_TOKEN** memory, size_t* n)
    { QUEX_NAME(token_queue_memory_switch)(this, memory, n); }
#   endif

#endif

QUEX_INLINE const char* 
QUEX_MEMBER(version)() const
{ return QUEX_NAME(version)((QUEX_TYPE_ANALYZER*)this); }

QUEX_INLINE void
QUEX_MEMBER(print_this)()
{ QUEX_NAME(print_this)(this); }

QUEX_INLINE bool
QUEX_MEMBER(byte_order_reversion)()
{ return QUEX_NAME(byte_order_reversion)(this); }

QUEX_INLINE void     
QUEX_MEMBER(byte_order_reversion_set)(bool Value)
{ QUEX_NAME(byte_order_reversion_set)(this, Value); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__MISC_I */
