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

    QUEX_INLINE uint8_t*
    QUEX_NAME(unicode_to_utf8)(QUEX_TYPE_CHARACTER  UCS_CharacterCode, uint8_t* utf8_result)
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
        uint8_t* p = utf8_result;
        /**/
        __quex_assert(UCS_CharacterCode >= (QUEX_TYPE_CHARACTER)0);

        /* cannot convert surrogate pairs */
        if (UCS_CharacterCode >= 0xd800 && UCS_CharacterCode <= 0xdfff) return 0x0;

        if (UCS_CharacterCode <= 0x0000007f) {
            *p = (uint8_t)UCS_CharacterCode;
            return p + 1;
        } else if (UCS_CharacterCode <= 0x000007ff) {
            p[0] = (uint8_t)(0xC0 | (UCS_CharacterCode >> 6)); 
            p[1] = (uint8_t)(0x80 | (UCS_CharacterCode & 0x3f));
            return p + 2;
        } else if (UCS_CharacterCode <= 0x0000ffff) {
            p[0] = (uint8_t)(0xE0 | UCS_CharacterCode           >> 12);
            p[1] = (uint8_t)(0x80 | (UCS_CharacterCode & 0xFFF) >> 6);
            p[2] = (uint8_t)(0x80 | (UCS_CharacterCode & 0x3F));
            return p + 3;
        } else if (UCS_CharacterCode <= 0x001fffff) {
            p[0] = (uint8_t)(0xF0 | UCS_CharacterCode >> 18);
            p[1] = (uint8_t)(0x80 | (UCS_CharacterCode & 0x3FFFF) >> 12);
            p[2] = (uint8_t)(0x80 | (UCS_CharacterCode & 0xFFF)   >> 6);
            p[3] = (uint8_t)(0x80 | (UCS_CharacterCode & 0x3F));
            return p + 4;
        } else {
            QUEX_ERROR_EXIT("Unicode Character out of range (> 0x1FFFFF).");
        }
        /* NOTE: Do not check here for forbitten UTF-8 characters.
         * They cannot appear here because we do proper conversion. */
    }

    QUEX_INLINE uint8_t*
    QUEX_NAME(unicode_to_utf8_string)(const QUEX_TYPE_CHARACTER*  Source, 
                                      size_t                      SourceSize, 
                                      uint8_t*                    Drain, 
                                      size_t                      DrainSize)
        /* RETURNS: Pointer to end of string, i.e. a pointer after the last
         *          element of the string.                                   */
    {
        const QUEX_TYPE_CHARACTER*  source_iterator = 0x0;
        const QUEX_TYPE_CHARACTER*  source_end = 0x0;
        uint8_t*                    drain_iterator = 0x0; 
        uint8_t*                    drain_end = 0x0;

        __quex_assert(Source != 0x0);
        __quex_assert(Drain != 0x0);

        drain_iterator = Drain;
        drain_end      = Drain  + DrainSize;
        source_end     = Source + SourceSize;

        for(source_iterator = Source; source_iterator < source_end; ++source_iterator) {
            if( drain_end - drain_iterator < (ptrdiff_t)7 ) break;
            drain_iterator = QUEX_NAME(unicode_to_utf8)(*source_iterator, drain_iterator);
        }

        return drain_iterator;
    }

    /* The following function exists for uniformity. */
    QUEX_INLINE uint8_t*
    QUEX_NAME(utf8_to_utf8_string)(const QUEX_TYPE_CHARACTER* Source, 
                                   size_t                     SourceSize, 
                                   uint8_t*                   Drain, 
                                   size_t                     DrainSize)
    {
        const size_t Size = SourceSize < DrainSize ? SourceSize : DrainSize;

        __QUEX_STD_memcpy((void*)Drain, (void*)Source, Size);
                          
        return Drain + Size;
    }

    QUEX_INLINE uint8_t*
    QUEX_NAME(utf16_to_utf8_string)(const QUEX_TYPE_CHARACTER* Source, 
                                    size_t                     SourceSize, 
                                    uint8_t*                   Drain, 
                                    size_t                     DrainSize)
    {
        const QUEX_TYPE_CHARACTER*  source_iterator = 0x0;
        const QUEX_TYPE_CHARACTER*  source_end = 0x0;
        uint8_t*                    drain_iterator = 0x0; 
        uint8_t*                    drain_end = 0x0;
        uint32_t                    x0 = (uint16_t)-1;
        uint32_t                    x1 = (uint16_t)-1;
        uint32_t                    unicode_value = 0;

        __quex_assert(Source != 0x0);
        __quex_assert(Drain != 0x0);

        drain_iterator = Drain;
        drain_end      = Drain  + DrainSize;
        source_end     = Source + SourceSize;

        for(source_iterator = Source; source_iterator < source_end; ++source_iterator) {
            /* If code is two 'words': First word == 0xD800 */
            if( *source_iterator >= 0xD800 && *source_iterator <= 0xDBFF ) {
                x0 = (uint32_t)(*source_iterator++ - 0xD800);
                x1 = (uint32_t)(*source_iterator   - 0xDC00);
                unicode_value = (uint32_t)((x0 << 10) + x1 + (uint32_t)0x10000);
            } else {
                unicode_value = (uint32_t)(*source_iterator);
            }
            if( drain_end - drain_iterator < (ptrdiff_t)7 ) break;
            drain_iterator = QUEX_NAME(unicode_to_utf8)((QUEX_TYPE_CHARACTER)unicode_value,
                                                        drain_iterator);
        }

        return drain_iterator;
    }

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__UNICODE_I */
