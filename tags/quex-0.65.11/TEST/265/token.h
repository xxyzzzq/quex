/* <<<QUEX-OPTIONS>>>
 *   --token-id-prefix       TKN_
 *   --token-class           Common::Token
 *   --token-id-type         uint32_t
 *   --buffer-element-type   uint32_t
 *   --lexeme-null-object    ::Common::LexemeNullObject
 * <<<QUEX-OPTIONS>>>
 */
/* -*- C++ -*-   vim: set syntax=cpp: 
 * (C) 2004-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY
 */
#ifndef __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__COMMON___TOKEN
#define __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__COMMON___TOKEN

/* For '--token-class-only' the following option may not come directly
 * from the configuration file.                                        */
#ifndef    __QUEX_OPTION_PLAIN_C
#   define __QUEX_OPTION_PLAIN_C
#endif
#include <quex/code_base/definitions>
#include <quex/code_base/asserts>
#include <quex/code_base/compatibility/stdint.h>

/* LexemeNull object may be used for 'take_text'. */

#if ! defined(QUEX_NAME_TOKEN)
#   if defined(__QUEX_OPTION_PLAIN_C)
#      define QUEX_NAME_TOKEN(NAME)   Common_Token_ ## NAME
#   else
#      define QUEX_NAME_TOKEN(NAME)   Common_Token_ ## NAME
#   endif
#   define __QUEX_SIGNAL_DEFINED_QUEX_NAME_TOKEN_COMMON___TOKEN
#endif

extern uint32_t  Common_LexemeNullObject;






       #include <stdio.h>
       #include <string.h>

       struct Common_Token_tag;

       extern const char* 
       Common_Token_get_string(struct Common_Token_tag* me,  char*  buffer, size_t   BufferSize); 

       extern const char* 
       Common_Token_pretty_char_text(struct Common_Token_tag* me, char*   buffer, size_t  BufferSize); 

#      if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
       extern const wchar_t* 
       Common_Token_pretty_wchar_text(struct Common_Token_tag* me, wchar_t*  buffer, size_t BufferSize); 
#      endif


#if defined(QUEX_CONVERTER_CHAR_DEF)
#   undef  __QUEX_CONVERTER_CHAR_DEF
#   undef  __QUEX_CONVERTER_STRING_DEF
#   undef  QUEX_CONVERTER_CHAR_DEF
#   undef  QUEX_CONVERTER_STRING_DEF
#   undef  __QUEX_CONVERTER_CHAR
#   undef  __QUEX_CONVERTER_STRING
#   undef  QUEX_CONVERTER_CHAR
#   undef  QUEX_CONVERTER_STRING
#   undef  QUEX_NAMESPACE_MAIN_OPEN               
#   undef  QUEX_NAMESPACE_MAIN_CLOSE              
#   undef  QUEX_TYPE_LEXATOM
#   define __QUEX_SIGNAL_UNDEFINED_CONVERTER_MACROS_COMMON___TOKEN
#endif
#define    __QUEX_CONVERTER_CHAR_DEF(FROM, TO)    Common_Token ##FROM ## _to_ ## TO ## _character
#define    __QUEX_CONVERTER_STRING_DEF(FROM, TO)  Common_Token ##FROM ## _to_ ## TO
#define    QUEX_CONVERTER_CHAR_DEF(FROM, TO)      __QUEX_CONVERTER_CHAR_DEF(FROM, TO)
#define    QUEX_CONVERTER_STRING_DEF(FROM, TO)    __QUEX_CONVERTER_STRING_DEF(FROM, TO)
#define    __QUEX_CONVERTER_CHAR(FROM, TO)        Common_Token ##FROM ## _to_ ## TO ## _character
#define    __QUEX_CONVERTER_STRING(FROM, TO)      Common_Token ##FROM ## _to_ ## TO
#define    QUEX_CONVERTER_CHAR(FROM, TO)          __QUEX_CONVERTER_CHAR(FROM, TO)
#define    QUEX_CONVERTER_STRING(FROM, TO)        __QUEX_CONVERTER_STRING(FROM, TO)
#define    QUEX_NAMESPACE_MAIN_OPEN               
#define    QUEX_NAMESPACE_MAIN_CLOSE              
#define    QUEX_TYPE_LEXATOM                uint32_t

#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__TMP_DISABLED
#include <quex/code_base/converter_helper/from-unicode-buffer>

#undef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__TMP_DISABLED

#undef     __QUEX_CONVERTER_CHAR_DEF
#undef     __QUEX_CONVERTER_STRING_DEF
#undef     QUEX_CONVERTER_CHAR_DEF
#undef     QUEX_CONVERTER_STRING_DEF
#undef     __QUEX_CONVERTER_CHAR
#undef     __QUEX_CONVERTER_STRING
#undef     QUEX_CONVERTER_CHAR
#undef     QUEX_CONVERTER_STRING
#undef     QUEX_NAMESPACE_MAIN_OPEN               
#undef     QUEX_NAMESPACE_MAIN_CLOSE              
#undef     QUEX_TYPE_LEXATOM
#if defined(__QUEX_SIGNAL_UNDEFINED_CONVERTER_MACROS_COMMON___TOKEN)
#   define __QUEX_CONVERTER_CHAR_DEF    __QUEX_CONVERTER_CHAR_DEF_BACKUP
#   define __QUEX_CONVERTER_STRING_DEF  __QUEX_CONVERTER_STRING_DEF_BACKUP
#   define QUEX_CONVERTER_CHAR_DEF      QUEX_CONVERTER_CHAR_DEF_BACKUP
#   define QUEX_CONVERTER_STRING_DEF    QUEX_CONVERTER_STRING_DEF_BACKUP
#   define __QUEX_CONVERTER_CHAR        __QUEX_CONVERTER_CHAR_BACKUP
#   define __QUEX_CONVERTER_STRING      __QUEX_CONVERTER_STRING_BACKUP
#   define QUEX_CONVERTER_CHAR          QUEX_CONVERTER_CHAR_BACKUP
#   define QUEX_CONVERTER_STRING        QUEX_CONVERTER_STRING_BACKUP
#   define QUEX_NAMESPACE_MAIN_OPEN     QUEX_NAMESPACE_MAIN_OPEN_BACKUP               
#   define QUEX_NAMESPACE_MAIN_CLOSE    QUEX_NAMESPACE_MAIN_CLOSE_BACKUP              
#   define QUEX_TYPE_LEXATOM          QUEX_TYPE_LEXATOM_BACKUP
#endif

   

/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA */

 
typedef struct Common_Token_tag {
    uint32_t    _id;

    const uint32_t* text;
    size_t                     number;
/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA */


#   ifdef     QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        QUEX_TYPE_TOKEN_LINE_N    _line_n;
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        QUEX_TYPE_TOKEN_COLUMN_N  _column_n;
#       endif
#   endif


       /*
        */
   

/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA */

} Common_Token;

QUEX_INLINE void Common_Token_construct(Common_Token*);
QUEX_INLINE void Common_Token_copy_construct(Common_Token*, 
                                             const Common_Token*);
QUEX_INLINE void Common_Token_copy(Common_Token*, const Common_Token*);
QUEX_INLINE void Common_Token_destruct(Common_Token*);

/* NOTE: Setters and getters as in the C++ version of the token class are not
 *       necessary, since the members are accessed directly.                   */

QUEX_INLINE void 
Common_Token_set(Common_Token*            __this, 
                 const uint32_t ID);

extern const char*  Common_Token_map_id_to_name(const uint32_t);

QUEX_INLINE bool 
Common_Token_take_text(Common_Token*              __this, 
                       void*        analyzer, 
                       const uint32_t* Begin, const uint32_t* End);

#ifdef QUEX_OPTION_TOKEN_REPETITION_SUPPORT
QUEX_INLINE size_t Common_Token_repetition_n_get(Common_Token*);
QUEX_INLINE void   Common_Token_repetition_n_set(Common_Token*, size_t);
#endif /* QUEX_OPTION_TOKEN_REPETITION_SUPPORT */


#if defined(__QUEX_SIGNAL_DEFINED_QUEX_NAME_TOKEN_COMMON___TOKEN)
#   undef QUEX_NAME_TOKEN
#endif


#endif /* __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__COMMON___TOKEN */

