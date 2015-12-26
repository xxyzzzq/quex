QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO(user_constructor)
{
    QUEX_MAP_THIS_TO_ME(QUEX_TYPE_ANALYZER) 
    (void)me;

$$CONSTRUCTOR_MODE_DB_INITIALIZATION_CODE$$

#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
/* START: User's constructor extensions _______________________________________*/
$$CONSTRUCTOR_EXTENSTION$$
/* END: _______________________________________________________________________*/
#undef self
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO(user_reset) 
{
    QUEX_MAP_THIS_TO_ME(QUEX_TYPE_ANALYZER)
    (void)me;

#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
/* START: User's 'reset' ______________________________________________________*/
$$RESET_EXTENSIONS$$
/* END: _______________________________________________________________________*/
#undef self
}

#ifdef QUEX_OPTION_INCLUDE_STACK

QUEX_INLINE bool
QUEX_MEMBER_FUNCTIONO2(user_memento_pack, 
                       const char*         InputName, 
                       QUEX_NAME(Memento)* memento) 
{
    QUEX_MAP_THIS_TO_ME(QUEX_TYPE_ANALYZER) 
    (void)me; (void)memento; (void)InputName;

#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
/* START: User's memento 'pack' _______________________________________________*/
$$MEMENTO_EXTENSIONS_PACK$$
/* END: _______________________________________________________________________*/
#undef self
    return true;
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTIONO1(user_memento_unpack, QUEX_NAME(Memento)*  memento)
{
    QUEX_MAP_THIS_TO_ME(QUEX_TYPE_ANALYZER) 
    (void)me; (void)memento;

#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
/* START: User's memento 'unpack' _____________________________________________*/
$$MEMENTO_EXTENSIONS_UNPACK$$
/* END: _______________________________________________________________________*/
#undef self
}
#endif /* QUEX_OPTION_INCLUDE_STACK */

QUEX_NAMESPACE_MAIN_CLOSE

#if defined(__QUEX_OPTION_CONVERTER_HELPER)
#   include "$$CONVERTER_HELPER_I$$"
#else
#   include "quex/code_base/converter_helper/from-unicode-buffer.i"
#endif
#include <quex/code_base/analyzer/headers.i>

