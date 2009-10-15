/* The following cannot be protected against multiple inclusion. It is possible
 * that it is defined multiple times for different lexical analyzers.
 */
#include <quex/code_base/definitions>

#ifndef QUEX_TYPE_TOKEN_WITH_NAMESPACE
#   error "File requires definition of macro QUEX_TYPE_TOKEN_WITH_NAMESPACE"
#endif
#ifndef QUEX_TYPE_MEMENTO
#   error "File requires definition of macro QUEX_TYPE_MEMENTO"
#endif
#ifndef QUEX_TYPE_MEMENTO_TAG
#   error "File requires definition of macro QUEX_TYPE_MEMENTO_TAG"
#endif

QUEX_NAMESPACE_MAIN_OPEN

#ifdef __QUEX_OPTION_TOKEN_POLICY_IS_QUEUE_BASED
QUEX_INLINE QUEX_TYPE_TOKEN_WITH_NAMESPACE* 
QUEX_FIX3(MemoryManager_, QUEX_TYPE_STR_TOKEN_COMPLETE, _allocate)(const size_t N)
{
    const size_t     MemorySize = sizeof(QUEX_TYPE_TOKEN_WITH_NAMESPACE) * N;
    return (QUEX_TYPE_TOKEN_WITH_NAMESPACE*)__QUEX_ALLOCATE_MEMORY(MemorySize);
}

QUEX_INLINE void 
QUEX_FIX3(MemoryManager_, QUEX_TYPE_STR_TOKEN_COMPLETE, _free)(QUEX_TYPE_TOKEN_WITH_NAMESPACE* memory)
{
    if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); 
}
#endif

#if defined (QUEX_OPTION_INCLUDE_STACK)
/* NOTE: The macro 'QUEX_MACRO_STRING_CONCATINATE' is used to generate a function
 *       name. For example, if the macro QUEX_TYPE_MEMENTO is defined as 'LexerMemento',
 *       then the macro call
 *
 *           QUEX_FIX3(MemoryManager_, QUEX_TYPE_MEMENTO, _allocate)
 *
 *       generates the function name:
 *
 *           MemoryManager_LexerMemento_allocate
 *
 *       Results of C-Preprocessing can always be viewed with 'gcc -E'.
 *                                                                                    */
QUEX_INLINE QUEX_TYPE_MEMENTO*
QUEX_FIX3(MemoryManager_, QUEX_TYPE_MEMENTO, _allocate)()
{
    const size_t     MemorySize = sizeof(QUEX_TYPE_MEMENTO);
    return (QUEX_TYPE_MEMENTO*)__QUEX_ALLOCATE_MEMORY(MemorySize);
}

QUEX_INLINE void
QUEX_FIX3(MemoryManager_, QUEX_TYPE_MEMENTO, _free)(struct QUEX_TYPE_MEMENTO_TAG* memory)
{ if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE


