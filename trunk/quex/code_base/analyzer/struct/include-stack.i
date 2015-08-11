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

    QUEX_INLINE void    
    QUEX_NAME(include_push_file_name)(QUEX_TYPE_ANALYZER*      me,
                                      QUEX_TYPE_CHARACTER*     FileName,
                                      const QUEX_NAME(Mode)*   mode, 
                                      const char*              CharacterCodecName /* = 0x0 */)
    {
        __QUEX_STD_FILE*   fh = __QUEX_STD_fopen(Filename, "rb");
        /* The Optional_InputHandle = 0x0, which indicates that FileName tells how to 
         * open the input stream.                                                       */
        QUEX_NAME(include_push_FILE)(me, 0x0, FileName, mode, CharacterCodecName);
    }

    QUEX_INLINE void    
    QUEX_NAME(include_push_FILE)(QUEX_TYPE_ANALYZER*      me,
                                 __QUEX_STD_FILE*         fh,
                                 const QUEX_NAME(Mode)*   mode, 
                                 const char*              CharacterCodecName /* = 0x0 */)
    {
        QUEX_NAME(include_push)(me, ByteLoader_FILE_new(fh), mode, CharacterCodecName);
    }

#   ifndef __QUEX_OPTION_PLAIN_C
    QUEX_INLINE void
    QUEX_NAME(include_push_istream)(QUEX_TYPE_ANALYZER*      me,
                                    std::istream*            istream_p, 
                                    const QUEX_NAME(Mode)*   mode, 
                                    const char*              CharacterCodecName /* = 0x0 */)
    {
        QUEX_NAME(include_push)(me, ByteLoader_stream_new(istream_p), mode, CharacterCodecName);
    }
#   endif

#   if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
    QUEX_INLINE void
    QUEX_NAME(include_push_wistream)(QUEX_TYPE_ANALYZER*      me,
                                    std::wistream*           istream_p, 
                                    const QUEX_NAME(Mode)*   mode, 
                                    const char*              CharacterCodecName /* = 0x0 */)
    {
        ByteLoader* byte_loader = ByteLoader_stream_new(istream_p); 

        QUEX_NAME(include_push_basic)(me, byte_loader,
                                      mode, CharacterCodecName);
    }
#   endif

    QUEX_INLINE void
    QUEX_NAME(include_stack_delete)(QUEX_TYPE_ANALYZER* me) 
    {
        while( me->_parent_memento != 0x0 ) {
            if( QUEX_NAME(include_pop)(me) == false ) {
                QUEX_ERROR_EXIT("Error during deletion of include stack.");
            }
        }
    }

#if ! defined( __QUEX_OPTION_PLAIN_C )
    QUEX_INLINE void    
    QUEX_MEMBER(include_push)(QUEX_TYPE_CHARACTER*   InputName,
                              const QUEX_NAME(Mode)* Mode, 
                              const char*            CharacterCodecName /* = 0x0 */)
    { QUEX_NAME(include_push_file_name)(this, InputName, Mode, CharacterCodecName); }

    QUEX_INLINE void    
    QUEX_MEMBER(include_push)(__QUEX_STD_FILE*       fh,
                              const QUEX_NAME(Mode)* Mode, 
                              const char*            CharacterCodecName /* = 0x0 */)
    { QUEX_NAME(include_push_FILE)(this, fh, Mode, CharacterCodecName); }

    QUEX_INLINE void    
    QUEX_MEMBER(include_push)(std::istream*          stream_p,
                              const QUEX_NAME(Mode)* Mode, 
                              const char*            CharacterCodecName /* = 0x0 */)
    { QUEX_NAME(include_push_istream)(this, stream_p, Mode, CharacterCodecName); }

    QUEX_INLINE void    
    QUEX_MEMBER(include_push)(std::wistream*         stream_p,
                              const QUEX_NAME(Mode)* Mode, 
                              const char*            CharacterCodecName /* = 0x0 */)
    { QUEX_NAME(include_push_wistream)(this, stream_p, Mode, CharacterCodecName); }

    QUEX_INLINE bool
    QUEX_MEMBER(include_pop)() 
    { return QUEX_NAME(include_pop)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(include_stack_delete)() 
    { QUEX_NAME(include_stack_delete)(this); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__INCLUDE_STACK_I */
