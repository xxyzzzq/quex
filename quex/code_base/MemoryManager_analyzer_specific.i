/* The following cannot be protected against multiple inclusion. It is possible
 * that it is defined multiple times for different lexical analyzers.
 */
#include <quex/code_base/definitions>

#ifndef QUEX_TYPE_TOKEN
#   error "File requires definition of macro QUEX_TYPE_TOKEN"
#endif
#ifndef CLASS_MEMENTO
#   error "File requires definition of macro CLASS_MEMENTO"
#endif
#ifndef CLASS_MEMENTO_TAG
#   error "File requires definition of macro CLASS_MEMENTO_TAG"
#endif

namespace quex {
#   if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE) || defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
    QUEX_INLINE QUEX_TYPE_TOKEN* 
    QUEX_NAMER(MemoryManager_, QUEX_TYPE_STR_TOKEN_COMPLETE, _allocate)(const size_t N)
    {
        const size_t     MemorySize = sizeof(QUEX_TYPE_TOKEN) * N;
        return (QUEX_TYPE_TOKEN*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }

    QUEX_INLINE void 
    QUEX_NAMER(MemoryManager_, QUEX_TYPE_STR_TOKEN_COMPLETE, _free)(QUEX_TYPE_TOKEN* memory)
    {
        if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); 
    }
#   endif

#   if defined (QUEX_OPTION_INCLUDE_STACK)
    /* NOTE: The macro 'QUEX_MACRO_STRING_CONCATINATE' is used to generate a function
     *       name. For example, if the macro CLASS_MEMENTO is defined as 'LexerMemento',
     *       then the macro call
     *
     *           QUEX_NAMER(MemoryManager_, CLASS_MEMENTO, _allocate)
     *
     *       generates the function name:
     *
     *           MemoryManager_LexerMemento_allocate
     *
     *       Results of C-Preprocessing can always be viewed with 'gcc -E'.
     *                                                                                    */
    QUEX_INLINE CLASS_MEMENTO*
    QUEX_NAMER(MemoryManager_, CLASS_MEMENTO, _allocate)()
    {
        const size_t     MemorySize = sizeof(CLASS_MEMENTO);
        return (CLASS_MEMENTO*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }

    QUEX_INLINE void
    QUEX_NAMER(MemoryManager_, CLASS_MEMENTO, _free)(CLASS_MEMENTO* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }
#   endif
}


