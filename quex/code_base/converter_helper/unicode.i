/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: Parts of the following functions have been derived from 
 *                  segments of the utf8 conversion library of Alexey 
 *                  Vatchenko <av@bsdua.org>.    
 *
 * (C) 2005-2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARANTY                                                      */

#ifndef __QUEX_INCLUDE_GUARD__UNICODE_I
#define __QUEX_INCLUDE_GUARD__UNICODE_I

#include <quex/code_base/definitions>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(unicode_to_utf8)(const QUEX_TYPE_CHARACTER**  input_pp, 
                           uint8_t**                    output_pp)
{
    /* PURPOSE: This function converts the specified unicode character
     *          into its utf8 representation. The result is stored
     *          at the location where utf8_result points to. Thus, the
     *          user has to make sure, that enough space is allocated!
     *
     * NOTE:    For general applicability let utf8_result point to a space
     *          of 7 bytes! This way you can store always a terminating
     *          zero after the last byte of the representation.
     *
     * RETURNS: Pointer to the fist position after the last character.      */
    uint32_t  Unicode = **input_pp;
    /**/

    if (Unicode <= 0x0000007f) {
        *(*output_pp)++ = (uint8_t)Unicode;
    } else if (Unicode <= 0x000007ff) {
        *(*output_pp)++ = (uint8_t)(0xC0 | (Unicode >> 6)); 
        *(*output_pp)++ = (uint8_t)(0x80 | (Unicode & 0x3f));
    } else if (Unicode <= 0x0000ffff) {
        *(*output_pp)++ = (uint8_t)(0xE0 | Unicode           >> 12);
        *(*output_pp)++ = (uint8_t)(0x80 | (Unicode & 0xFFF) >> 6);
        *(*output_pp)++ = (uint8_t)(0x80 | (Unicode & 0x3F));
    } else { 
        /* Assume that only character appear, that are defined in unicode. */
        __quex_assert(Unicode <= (QUEX_TYPE_CHARACTER)0x1FFFFF);
        /* No surrogate pairs (They are reserved even in non-utf16).       */
        __quex_assert(! (Unicode >= 0xd800 && Unicode <= 0xdfff) );

        *(*output_pp)++ = (uint8_t)(0xF0 | Unicode >> 18);
        *(*output_pp)++ = (uint8_t)(0x80 | (Unicode & 0x3FFFF) >> 12);
        *(*output_pp)++ = (uint8_t)(0x80 | (Unicode & 0xFFF)   >> 6);
        *(*output_pp)++ = (uint8_t)(0x80 | (Unicode & 0x3F));
    }
    /* NOTE: Do not check here for forbitten UTF-8 characters.
     * They cannot appear here because we do proper conversion. */
    ++(*input_pp);
}

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
QUEX_INLINE void
QUEX_NAME(unicode_to_wchar)(const QUEX_TYPE_CHARACTER**  input_pp, 
                            wchar_t**                    output_pp)
{
    *(*output_pp)++ = (wchar_t)(*(*input_pp)++);
}
#endif /* not __QUEX_OPTION_WCHAR_T_DISABLED */

QUEX_NAMESPACE_MAIN_CLOSE

#define __QUEX_CONVERTER_FROM   unicode
#include <quex/code_base/converter_helper/base.gi>

#endif /* __QUEX_INCLUDE_GUARD__UNICODE_I */
