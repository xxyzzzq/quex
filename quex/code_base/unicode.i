/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: The following functions have been derived from segments of the
 *                  utf8 conversion library of Alexey Vatchenko <av@bsdua.org>.    
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */

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
         * RETURNS: Number of bytes that was required to convert the character
         *          into its utf8 representation.                               */
        const uint8_t NEXT	= 0x80;
        const uint8_t LEN2	= 0xc0;
        const uint8_t LEN3	= 0xe0;
        const uint8_t LEN4	= 0xf0;
        const uint8_t LEN5	= 0xf8;
        const uint8_t LEN6	= 0xfc;
        /**/
        uint8_t* p = utf8_result;
        size_t   n = 0;
        /**/
        /* Split explicitly  be safe in different byte endian evironments. */
        uint8_t byte3 = (uint8_t)((UCS_CharacterCode & 0xFF));
        uint8_t byte2 = (uint8_t)((UCS_CharacterCode & 0xFF00) >> 8);
        uint8_t byte1 = (uint8_t)((UCS_CharacterCode & 0xFF0000) >> 16);
        uint8_t byte0 = (uint8_t)((UCS_CharacterCode & 0xFF000000) >> 24);

        __quex_assert(UCS_CharacterCode >= (QUEX_TYPE_CHARACTER)0);

        /* cannot convert surrogate pairs */
        if (UCS_CharacterCode >= 0xd800 && UCS_CharacterCode <= 0xdfff) return 0x0;

        /* Determine number of bytes in the utf8 representation of the character */
        if      (UCS_CharacterCode <= 0x0000007f)       n = 1;
        else if (UCS_CharacterCode <= 0x000007ff)       n = 2;
        else if (UCS_CharacterCode <= 0x0000ffff)       n = 3;
        else if (UCS_CharacterCode <= 0x001fffff)       n = 4;
        else if (UCS_CharacterCode <= 0x03ffffff)       n = 5;
        else /* if (UCS_CharacterCode <= 0x7fffffff) */ n = 6;

        switch (n) {
        case 1:
            *p = (uint8_t)UCS_CharacterCode;
            break;

        case 2:
            p[1] = (uint8_t)(NEXT | (byte3 & 0x3f));
            p[0] = (uint8_t)(LEN2 | (byte3 >> 6) | ((byte2 & (uint8_t)0x07) << 2));
            break;

        case 3:
            p[2] = (uint8_t)(NEXT | (byte3 & (uint8_t)0x3f));
            p[1] = (uint8_t)(NEXT | (byte3 >> 6) | ((byte2 & (uint8_t)0x0f) << 2));
            p[0] = (uint8_t)(LEN3 | ((byte2 & (uint8_t)0xf0) >> 4));
            break;

        case 4:
            p[3] = (uint8_t)(NEXT | (byte3 & (uint8_t)0x3f));
            p[2] = (uint8_t)(NEXT | (byte3 >> 6) | ((byte2 & 0x0f) << 2));
            p[1] = (uint8_t)(NEXT | ((byte2 & 0xf0) >> 4) | ((byte1 & 0x03) << 4));
            p[0] = (uint8_t)(LEN4 | ((byte1 & 0x1f) >> 2));
            break;

        case 5:
            p[4] = (uint8_t)(NEXT | (byte3 & (uint8_t)0x3f));
            p[3] = (uint8_t)(NEXT | (byte3 >> 6) | ((byte2 & 0x0f) << 2));
            p[2] = (uint8_t)(NEXT | ((byte2 & 0xf0) >> 4) | ((byte1 & 0x03) << 4));
            p[1] = (uint8_t)(NEXT | (byte1 >> 2));
            p[0] = (uint8_t)(LEN5 | (byte0 & 0x03));
            break;

        case 6:
            p[5] = (uint8_t)(NEXT | (byte3 & (uint8_t)0x3f));
            p[4] = (uint8_t)(NEXT | (byte3 >> 6) | ((byte2 & 0x0f) << 2));
            p[3] = (uint8_t)(NEXT | (byte2 >> 4) | ((byte1 & 0x03) << 4));
            p[2] = (uint8_t)(NEXT | (byte1 >> 2));
            p[1] = (uint8_t)(NEXT | (byte0 & (uint8_t)0x3f));
            p[0] = (uint8_t)(LEN6 | ((byte0 & (uint8_t)0x40) >> 6));
            break;
        }

        /* NOTE: Do not check here for forbitten UTF-8 characters.
         * They cannot appear here because we do proper conversion. */
        return p + n;
    }

    QUEX_INLINE uint8_t*
    QUEX_NAME(unicode_to_utf8_string)(QUEX_TYPE_CHARACTER *Source, size_t SourceSize, uint8_t *Drain, size_t DrainSize)
    {
        QUEX_TYPE_CHARACTER*  source_iterator = 0x0;
        QUEX_TYPE_CHARACTER*  source_end = 0x0;
        uint8_t*              drain_iterator = 0x0; 
        uint8_t*              drain_end = 0x0;

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


QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__UNICODE_I */
