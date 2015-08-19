#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

void
QUEX_MEMBER_FUNCTION(user_constructor, )
{
    (void)this;
$$CONSTRUCTOR_MODE_DB_INITIALIZATION_CODE$$

#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
/* START: User's constructor extensions _______________________________________*/
$$CONSTRUCTOR_EXTENSTION$$
/* END: _______________________________________________________________________*/
#undef self
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTION(user_reset, ) 
{
    (void)this;
/* START: User's 'reset' ______________________________________________________*/
$$MEMENTO_EXTENSIONS_PACK$$
/* END: _______________________________________________________________________*/
}

#ifdef QUEX_OPTION_INCLUDE_STACK

QUEX_INLINE void
QUEX_MEMBER_FUNCTION1(user_memento_pack, , QUEX_NAME(Memento)* memento) 
{
    (void)this; (void)memento;

/* START: User's memento 'pack' _______________________________________________*/
$$MEMENTO_EXTENSIONS_PACK$$
/* END: _______________________________________________________________________*/
}

QUEX_INLINE void
QUEX_MEMBER_FUNCTION1(user_memento_unpack, , QUEX_NAME(Memento)*  memento)
{
    (void)this; (void)memento;

/* START: User's memento 'unpack' _____________________________________________*/
$$MEMENTO_EXTENSIONS_UNPACK$$
/* END: _______________________________________________________________________*/
}
#endif /* QUEX_OPTION_INCLUDE_STACK */

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#if defined(__QUEX_OPTION_CONVERTER_HELPER)
#   include "$$CONVERTER_HELPER_I$$"
#else
#   include "quex/code_base/converter_helper/from-unicode-buffer.i"
#endif
#include <quex/code_base/analyzer/headers.i>

