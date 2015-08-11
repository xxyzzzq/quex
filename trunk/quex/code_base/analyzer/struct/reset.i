/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                   */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I

#include <quex/code_base/buffer/Buffer.i>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN


QUEX_INLINE void
QUEX_NAME(reset_file_name)(QUEX_TYPE_ANALYZER*  me,
                           const char*          FileName, 
                           const char*          CharacterEncodingName /* = 0x0 */) 
{
    /* Prefer FILE* based byte-loaders, because turn low-level buffering can be
     * turned off.                                                               */
    __QUEX_STD_FILE*   fh = __QUEX_STD_fopen(Filename, "rb");

    /* ByteLoader will overtake ownership over 'fh', so we do not need to 
     * take care over 'free' and 'fclose'.                                       */
    QUEX_NAME(reset_FILE)(me, fh, CharacterEncodingName);
}

QUEX_INLINE void
QUEX_NAME(reset_FILE)(QUEX_TYPE_ANALYZER*  me,
                      __QUEX_STD_FILE*     fh, 
                      const char*          CharacterEncodingName /* = 0x0 */) 
{
    QUEX_NAME(reset_basic)(me, 
                           ByteLoader_FILE_new(fh),
                           CharacterEncodingName, 
                           QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void
QUEX_NAME(reset_istream)(QUEX_TYPE_ANALYZER*  me,
                         std::istream*        istream_p, 
                         const char*          CharacterEncodingName /* = 0x0 */) 
{
    QUEX_NAME(reset_basic)(me, 
                           ByteLoader_stream_new(istream_p),
                           CharacterEncodingName, 
                           QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
}
#endif

#if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE void
QUEX_NAME(reset_wistream)(QUEX_TYPE_ANALYZER*  me,
                          std::wistream*       istream_p, 
                          const char*          CharacterEncodingName /* = 0x0 */) 
{
    QUEX_NAME(reset_basic)(me, 
                           ByteLoader_stream_new(istream_p),
                           CharacterEncodingName, 
                           QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
}
#endif


QUEX_INLINE void 
QUEX_NAME(reset_plain)(QUEX_TYPE_ANALYZER*  me,
                       const char*          CharacterEncodingName /* = 0x0 */)
{ QUEX_NAME(reset)(me, (FILE*)0x0, CharacterEncodingName); }

#if ! defined(__QUEX_OPTION_PLAIN_C)
inline void
QUEX_MEMBER(reset)(QUEX_NAME(BufferFiller)* filler, const char* CharacterEncodingName /* = 0x0 */) 
{
    QUEX_NAME(reset_basic)(this, filler,
                           CharacterEncodingName, 
                           QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
}
inline void
QUEX_MEMBER(reset)(FILE* input_handle, const char* CharacterEncodingName /* = 0x0 */) 
{ QUEX_NAME(reset_FILE)(this, input_handle, CharacterEncodingName); }

inline void
QUEX_MEMBER(reset)(std:istream* input_handle, const char* CharacterEncodingName /* = 0x0 */) 
{ QUEX_NAME(reset_istream)(this, input_handle, CharacterEncodingName); }

#if defined(__QUEX_OPTION_WCHAR_T) && ! defined(__QUEX_OPTION_PLAIN_C)
inline void
QUEX_MEMBER(reset)(std::wistream* input_handle, const char* CharacterEncodingName /* = 0x0 */) 
{ QUEX_NAME(reset_wistream)(this, input_handle, CharacterEncodingName); }
#endif

QUEX_INLINE QUEX_TYPE_CHARACTER*
QUEX_MEMBER(reset_buffer)(QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
                          size_t               BufferMemorySize,
                          QUEX_TYPE_CHARACTER* BufferEndOfContentP,  
                          const char*          CharacterEncodingName /* = 0x0 */) 
{ return QUEX_NAME(reset_buffer)(this, BufferMemoryBegin, BufferMemorySize, BufferEndOfContentP, CharacterEncodingName); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__STRUCT__RESET_I */
