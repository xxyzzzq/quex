import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from copy import copy
from quex.core_engine.interval_handling import Interval
from quex.frs_py.string_handling        import blue_print
from quex.frs_py.file_in                import write_safely_and_close, make_safe_identifier
from quex.input.setup                   import setup as Setup
from quex.input.setup_parser            import __prepare_file_name

LanguageDB = Setup.language_db

def do():
    if Setup.engine_character_encoding == "": return
    if Setup.engine_character_encoding_transformation_info in ["utf8-state-split", "utf16-state-split"]: return

    assert Setup.engine_character_encoding_transformation_info != None

    txt = write(Setup.engine_character_encoding_transformation_info, 
                Setup.engine_character_encoding)

    file_name = __prepare_file_name("-converter-%s" % Setup.engine_character_encoding)
    write_safely_and_close(file_name, txt) 

def write(UnicodeTrafoInfo, CodecName):
    """
    PURPOSE: Writes converters for conversion towards UTF8/UTF16/UCS2/UCS4.

    UnicodeTrafoInfo:

       Provides the information about the relation of character codes in a particular 
       coding to unicode character codes. It is provided in the following form:

       # Codec Values                 Unicode Values
       [ (Source0_Begin, Source0_End, TargetInterval0_Begin), 
         (Source1_Begin, Source1_End, TargetInterval1_Begin),
         (Source2_Begin, Source2_End, TargetInterval2_Begin), 
         ... 
       ]
    """
    codec_name = make_safe_identifier(CodecName)
    utf8_prolog,  utf8_function_body  = ConverterWriterUTF8().do(UnicodeTrafoInfo)
    # print "##utf16ct:"
    # for info in ConverterWriterUTF16().get_conversion_table(UnicodeTrafoInfo):
    #    print "##", info
    utf16_prolog, utf16_function_body = ConverterWriterUTF16().do(UnicodeTrafoInfo)
    # print "##END"
    dummy,        ucs4_function_body  = ConverterWriterUCS4().do(UnicodeTrafoInfo)

    # Provide only the constant which are necessary

    return blue_print(template_txt, 
                      [["$$CODEC$$",     CodecName],
                       ["$$PROLOG_UTF8$$", utf8_prolog],
                       ["$$BODY_UTF8$$",   utf8_function_body],
                       ["$$BODY_UTF16$$",  utf16_function_body],
                       ["$$BODY_UCS4$$",   ucs4_function_body]])

template_txt = \
"""
/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: Parts of the following utf8 conversion have been derived from 
 *                  segments of the utf8 conversion library of Alexey Vatchenko 
 *                  <av@bsdua.org>.    
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */

#ifndef __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_$$CODEC$$__
#define __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_$$CODEC$$__

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

#if ! defined(__QUEX_OPTION_PLAIN_C)
#   include <stdexcept>
namespace quex { 
#endif
QUEX_INLINE uint8_t*
Quex_$$CODEC$$_to_utf8(QUEX_TYPE_CHARACTER input, uint8_t* output)
{
$$PROLOG_UTF8$$
    uint32_t   unicode  = 0xFFFF;
    uint8_t*   p        = output;

    /* The unicode range simply does not go beyond 0x10FFFF */
    __quex_assert(input < 0x110000);
    /* If the following assert fails, then QUEX_TYPE_CHARACTER needs to be chosen
     * of 'unsigned' type, e.g. 'unsigned char' instead of 'char'.                */
    __quex_assert(input >= 0);

#if 0
#   if defined(__QUEX_OPTION_LITTLE_ENDIAN)
#   define QUEX_BYTE_0  (*( ((uint8_t*)&unicode) + 3 ))
#   define QUEX_BYTE_1  (*( ((uint8_t*)&unicode) + 2 ))
#   define QUEX_BYTE_2  (*( ((uint8_t*)&unicode) + 1 ))
#   define QUEX_BYTE_3  (*( ((uint8_t*)&unicode) + 0 ))
#   else                             
#   define QUEX_BYTE_0  (*( ((uint8_t*)&unicode) + 0 ))
#   define QUEX_BYTE_1  (*( ((uint8_t*)&unicode) + 1 ))
#   define QUEX_BYTE_2  (*( ((uint8_t*)&unicode) + 2 ))
#   define QUEX_BYTE_3  (*( ((uint8_t*)&unicode) + 3 ))
#   endif
#else
#   define QUEX_BYTE_0  ((uint8_t)((unicode & 0xFF)))
#   define QUEX_BYTE_1  ((uint8_t)((unicode & 0xFF00) >> 8))
#   define QUEX_BYTE_2  ((uint8_t)((unicode & 0xFF0000) >> 16))
#   define QUEX_BYTE_3  ((uint8_t)((unicode & 0xFF000000) >> 24))
#endif

$$BODY_UTF8$$
    __quex_assert(p - output < (ptrdiff_t)7);
    __quex_assert(p > output);
    return p;

#   undef QUEX_BYTE_0 
#   undef QUEX_BYTE_1 
#   undef QUEX_BYTE_2 
#   undef QUEX_BYTE_3 
}

QUEX_INLINE uint32_t
/* DrainEnd pointer is not returned, since the increment is always '1' */
Quex_$$CODEC$$_to_ucs4(QUEX_TYPE_CHARACTER input)
{
    uint32_t  unicode = 0L;
$$BODY_UCS4$$
}

QUEX_INLINE uint16_t*
Quex_$$CODEC$$_to_utf16(QUEX_TYPE_CHARACTER input, uint16_t* p)
{
    uint32_t unicode = Quex_$$CODEC$$_to_ucs4(input);
$$BODY_UTF16$$
    return p;
}

QUEX_INLINE uint16_t
/* DrainEnd pointer is not returned, since the increment is always '1' */
Quex_$$CODEC$$_to_ucs2(QUEX_TYPE_CHARACTER input)
{
    return (uint16_t)Quex_$$CODEC$$_to_ucs4(input);
}

QUEX_INLINE uint8_t*
Quex_$$CODEC$$_to_utf8_string(QUEX_TYPE_CHARACTER* Source, size_t SourceSize, uint8_t *Drain, size_t DrainSize)
{
    QUEX_TYPE_CHARACTER *source_iterator, *source_end;
    uint8_t             *drain_iterator, *drain_end;

    __quex_assert(Source != 0x0);
    __quex_assert(Drain != 0x0);

    drain_iterator = Drain;
    drain_end      = Drain  + DrainSize;
    source_end     = Source + SourceSize;

    for(source_iterator = Source; source_iterator < source_end; ++source_iterator) {
        if( drain_end - drain_iterator < (ptrdiff_t)7 ) break;
        drain_iterator = Quex_$$CODEC$$_to_utf8(*source_iterator, drain_iterator);
    }

    return drain_iterator;
}

QUEX_INLINE uint16_t*
Quex_$$CODEC$$_to_utf16_string(QUEX_TYPE_CHARACTER* Source, size_t SourceSize, uint16_t *Drain, size_t DrainSize)
{
    QUEX_TYPE_CHARACTER *source_iterator, *source_end;
    uint16_t            *drain_iterator, *drain_end;

    __quex_assert(Source != 0x0);
    __quex_assert(Drain != 0x0);

    drain_iterator = Drain;
    drain_end      = Drain  + DrainSize;
    source_end     = Source + SourceSize;

    for(source_iterator = Source; source_iterator < source_end; ++source_iterator) {
        if( drain_end - drain_iterator < (ptrdiff_t)2 ) break;
        drain_iterator = Quex_$$CODEC$$_to_utf16(*source_iterator, drain_iterator);
    }

    return drain_iterator;
}

QUEX_INLINE uint16_t*
Quex_$$CODEC$$_to_ucs2_string(QUEX_TYPE_CHARACTER* Source, size_t SourceSize, uint16_t *Drain, size_t DrainSize)
{
    QUEX_TYPE_CHARACTER *source_iterator, *source_end;
    uint16_t            *drain_iterator, *drain_end;

    __quex_assert(Source != 0x0);
    __quex_assert(Drain != 0x0);

    drain_iterator = Drain;
    drain_end      = Drain  + DrainSize;
    source_end     = Source + SourceSize;

    for(source_iterator = Source; source_iterator < source_end; ++source_iterator) {
        if( drain_end == drain_iterator ) break;
        *drain_iterator++ = Quex_$$CODEC$$_to_ucs2(*source_iterator);
    }

    return drain_iterator;
}

QUEX_INLINE uint32_t*
Quex_$$CODEC$$_to_ucs4_string(QUEX_TYPE_CHARACTER* Source, size_t SourceSize, uint32_t *Drain, size_t DrainSize)
{
    QUEX_TYPE_CHARACTER *source_iterator, *source_end;
    uint32_t            *drain_iterator, *drain_end;

    __quex_assert(Source != 0x0);
    __quex_assert(Drain != 0x0);

    drain_iterator = Drain;
    drain_end      = Drain  + DrainSize;
    source_end     = Source + SourceSize;

    for(source_iterator = Source; source_iterator < source_end; ++source_iterator) {
        if( drain_end == drain_iterator ) break;
        *drain_iterator++ = Quex_$$CODEC$$_to_ucs4(*source_iterator);
    }

    return drain_iterator;
}


#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::string
Quex_$$CODEC$$_to_utf8_string(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    QUEX_TYPE_CHARACTER*  source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    QUEX_TYPE_CHARACTER*  source_end      = source_iterator + Source.length();
    uint8_t               drain[8];
    uint8_t*              drain_end = 0;
    std::string           result;

    for(; source_iterator != source_end; ++source_iterator) {
        drain_end = Quex_$$CODEC$$_to_utf8(*source_iterator, (uint8_t*)drain);
        *drain_end = (uint8_t)0;
        result += (char*)drain;
    }
    return result;
}

QUEX_INLINE std::basic_string<uint16_t>
Quex_$$CODEC$$_to_utf16_string(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    QUEX_TYPE_CHARACTER*         source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    QUEX_TYPE_CHARACTER*         source_end      = source_iterator + Source.length();
    uint16_t                     drain[8];
    uint16_t*                    drain_end = 0;
    std::basic_string<uint16_t>  result;

    for(; source_iterator != source_end; ++source_iterator) {
        drain_end = Quex_$$CODEC$$_to_utf16(*source_iterator, (uint16_t*)drain);
        *drain_end = (uint16_t)0;
        result += (uint16_t*)drain;
    }
    return result;
}

QUEX_INLINE std::basic_string<uint16_t>
Quex_$$CODEC$$_to_ucs2_string(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    QUEX_TYPE_CHARACTER*         source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    QUEX_TYPE_CHARACTER*         source_end      = source_iterator + Source.length();
    std::basic_string<uint16_t>  result;

    for(; source_iterator != source_end; ++source_iterator) {
        result += Quex_$$CODEC$$_to_ucs2(*source_iterator);
    }
    return result;
}

QUEX_INLINE std::basic_string<uint32_t>
Quex_$$CODEC$$_to_ucs4_string(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    QUEX_TYPE_CHARACTER*         source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    QUEX_TYPE_CHARACTER*         source_end      = source_iterator + Source.length();
    std::basic_string<uint32_t>  result;

    for(; source_iterator != source_end; ++source_iterator) {
        result += Quex_$$CODEC$$_to_ucs4(*source_iterator);
    }
    return result;
}


} // namespace quex
#endif

#endif /* __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_$$CODEC$$__ */

"""

class ConverterWriter:

    def do(self, UnicodeTrafoInfo, ProvidedConversionInfoF=False):
        """Creates code for a conversion to utf8 according to the conversion_table.
        """
        # The flag 'ProvidedConversionTableF' is only to be used for Unit Tests
        if ProvidedConversionInfoF: conversion_table = UnicodeTrafoInfo
        else:                       conversion_table = self.get_conversion_table(UnicodeTrafoInfo)

        # If the converter writer does not do a unicode conversion (even not for range 0),
        # then forget about the bracketing that was done earlier.
        __rely_on_ucs4_conversion_f = (self.get_unicode_range_conversion(conversion_table[0]) == "")

        # Make sure that the conversion table is sorted
        conversion_table.sort(lambda a, b: cmp(a.codec_interval_begin, b.codec_interval_begin))

        # Implement a binary bracketing of conversion domains
        def __bracket(conversion_list, CallerRangeIndex):
            txt = ""
            L = len(conversion_list)
            if   L == 1:
                txt += self.get_unicode_range_conversion(conversion_list[0])
                # The caller does have to implement an 'encoder
                if CallerRangeIndex != conversion_list[0].byte_format_range_index:
                    txt += self.get_byte_formatter(conversion_list[0].byte_format_range_index)
            else:
                # Determine wether all sub-ranges belong to the same utf8-range
                range_index = self.same_byte_format_range(conversion_list)

                # Bracket interval in the middle
                mid_index = int(float(L)/2)
                Middle    = "0x%06X" % conversion_list[mid_index].codec_interval_begin
                txt += LanguageDB["$if <"](Middle) 
                if range_index != -1: 
                    # If there is no 'unicode coversion' and all ranges belong to the 
                    # same byte formatting, then there is no need to bracket further:
                    if not __rely_on_ucs4_conversion_f:
                        txt += __bracket(conversion_list[:mid_index], range_index)
                        txt += LanguageDB["$endif-else"] + "\n"   
                        txt += __bracket(conversion_list[mid_index:], range_index)
                        txt += LanguageDB["$end-else"]
                    if CallerRangeIndex != range_index:
                        txt += self.get_byte_formatter(range_index)
                else:
                    txt += __bracket(conversion_list[:mid_index], range_index)
                    txt += LanguageDB["$endif-else"] + "\n"   
                    txt += __bracket(conversion_list[mid_index:], range_index)
                    txt += LanguageDB["$end-else"]

            return "    " + txt[:-1].replace("\n", "\n    ") + "\n"

        range_index = self.same_byte_format_range(conversion_table)
        txt         = __bracket(conversion_table, range_index)
        if range_index != -1: 
            # All codec ranges belong to the same byte format range.
            formatter_txt = "    " + self.get_byte_formatter(range_index)
            if __rely_on_ucs4_conversion_f:
                txt = formatter_txt
            else:
                txt += formatter_txt[:-1].replace("\n", "\n    ") + "\n"

        return self.get_prolog(conversion_table), txt

    def get_unicode_range_conversion(self, Info):
        assert isinstance(Info, ConversionInfo)

        # Conversion to Unicode
        return "unicode = 0x%06X + (input - 0x%06X);\n" % \
               (Info.codec_interval_begin_unicode, Info.codec_interval_begin)

    def same_byte_format_range(self, ConvInfoList):
        """RETURNS: >= 0   the common byte format range index.
                    == -1  not all infos belong to the same byte format range.
        """
        range_i = ConvInfoList[0].byte_format_range_index
        for info in ConvInfoList[1:]:
            if info.byte_format_range_index != range_i: return -1
        return ConvInfoList[0].byte_format_range_index

    def get_conversion_table(self, UnicodeTrafoInfo):
        """The UnicodeTrafoInfo tells what ranges in the codec are mapped to what ranges
           in unicode. The codec (e.g. UTF8/UTF16) has ranges of different byte
           formatting. 

           This function identifies ranges in the codec that:

              (1) map linearly to unicode
              (2) belong to the same byte format range.

           The result is a list of objects that identify those ranges in the codec
           and their relation to unicode. See definition of class ConversionInfo
           for a detailed description and a nice picture.
        """
        trafo_info  = copy(UnicodeTrafoInfo)
        border_list = self.get_byte_format_range_border_list()
        L = len(border_list)

        # Sort transform info database according to target range
        info_list = []
        trafo_info.sort(lambda a, b: cmp(a[2], b[2]))

        # Unicode Transformation Info -- A list of the following:
        for source_interval_begin, source_interval_end, target_interval_begin in trafo_info:

            # How does the target interval has to be split according to utf8-ranges?
            i = 0
            while source_interval_begin >= border_list[i]: 
                i += 1

            i -= 1
            ## print "##", i, source_interval_begin, border_list[i]
            # 'i' now stands on the first utf8_range that touches the source interval
            info = ConversionInfo(i, source_interval_begin, target_interval_begin)

            # NOTE: size of target interval = size of source interval
            remaining_size = source_interval_end - source_interval_begin

            ## print "## %i, %x, %x" % (i, source_interval_begin, source_interval_end)
            while i != L - 1 and remaining_size != 0:
                remaining_utf8_range_size = border_list[i+1] - source_interval_begin
                info.codec_interval_size  = min(remaining_utf8_range_size, remaining_size)
                ## print i, "%X: %x, %x" % (border_list[i+1], remaining_utf8_range_size, remaining_size)
                info_list.append(info)

                source_interval_begin  = border_list[i+1] 
                target_interval_begin += info.codec_interval_size
                remaining_size        -= info.codec_interval_size
                i += 1
                info = ConversionInfo(i, source_interval_begin, target_interval_begin)

            ## print "##", remaining_size
            if remaining_size != 0:
                info.codec_interval_size = remaining_size
                info_list.append(info)

        info_list.sort(lambda a, b: cmp(a.codec_interval_begin, b.codec_interval_begin))

        return info_list

class ConverterWriterUTF8(ConverterWriter):
    def get_prolog(self, ConvTable):
        # Define Constants which are required as 'Byte Heads' for UTF8 Strings
        unique_range_index_list = []
        for info in ConvTable:
            if info.byte_format_range_index not in unique_range_index_list:
                unique_range_index_list.append(info.byte_format_range_index)
        unique_range_index_list.sort()

        db = { 2: 0xc0, 3: 0xe0, 4: 0xf0, 5: 0xf8, 6: 0xfc }
        txt = ""
        if unique_range_index_list[-1] != 0:
            txt += "    const int NEXT = 0x80;\n"
        for index in unique_range_index_list:
            if index > 0:
                txt += "    const int LEN%i = 0x%03X;\n" % (index + 1, db[index + 1])
        return txt

    def get_byte_formatter(self, RangeIndex):
        # Byte Split
        return {
                0: 
                "*p = QUEX_BYTE_0; ++p;\n",
                1:
                "*(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);\n",

                2:
                "*(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);\n",

                3:
                "*(p++) = LEN4 | ((QUEX_BYTE_2 & 0x1f) >> 2);\n" + \
                "*(p++) = NEXT | ((QUEX_BYTE_1 & 0xf0) >> 4) | ((QUEX_BYTE_2 & 0x03) << 4);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);\n", 

                4:
                "*(p++) = LEN5 | QUEX_BYTE_3 & 0x03;\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_2 >> 2);\n" + \
                "*(p++) = NEXT | ((QUEX_BYTE_1 & 0xf0) >> 4) | ((QUEX_BYTE_2 & 0x03) << 4);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);\n",

                5:
                "*(p++) = LEN6 | ((QUEX_BYTE_3 & 0x40) >> 6);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_3 & 0x3f);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_2 >> 2);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_1 >> 4) | ((QUEX_BYTE_2 & 0x03) << 4);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);\n" + \
                "*(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);\n",

        }[RangeIndex] 

    def get_byte_format_range_border_list(self):
        """UTF8 covers the following regions with the corresponding numbers of bytes:
        
             0x00000000 - 0x0000007F: 1 byte  - 0xxxxxxx
             0x00000080 - 0x000007FF: 2 bytes - 110xxxxx 10xxxxxx
             0x00000800 - 0x0000FFFF: 3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
             0x00010000 - 0x001FFFFF: 4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
             0x00200000 - 0x03FFFFFF: 5 bytes ... 
             0x04000000 - 0x7FFFFFFF: 

            The range borders are, therefore, as mentioned in the return value.
        """
        return [ 0x0, 0x00000080, 0x00000800, 0x00010000, 0x00200000, 0x04000000, 0x80000000, sys.maxint] 

class ConverterWriterUTF16(ConverterWriter):
    def get_prolog(self, ConvTable):
        return ""

    def get_byte_formatter(self, RangeIndex):
        return { 0: "*p++ = unicode;\n",
                 1: "const uint16_t Offset_10bit_high = (uint16_t)((unicode - 0x10000) >> 10);\n"  + \
                    "const uint16_t Offset_10bit_low  = (uint16_t)((unicode - 0x10000) & 0x3FF);\n" + \
                    "*p++ = 0xD800 | offset_10bit_high;\n"
                    "*p++ = 0xDC00 | offset_10bit_low;\n",
                    }[RangeIndex]

    def get_byte_format_range_border_list(self):
        """UCS4 covers the whole range of unicode (extend 0x10FFFF to sys.maxint to be nice)."""
        return [ 0x0, 0x10000, sys.maxint] 
    
    def get_unicode_range_conversion(self, Info):
        # Take the unicode value via the UCS4 converter
        return ""

class ConverterWriterUCS4(ConverterWriter):
    def get_prolog(self, ConvTable):
        return ""

    def get_byte_formatter(self, RangeIndex):
        return "return unicode;\n"

    def get_byte_format_range_border_list(self):
        """UCS4 covers the whole range of unicode (extend 0x10FFFF to sys.maxint to be nice)."""
        return [ 0x0, sys.maxint] 

class ConversionInfo:
    """A given interval in the codec corresponds to a certain byte formatting
       range in the target encoding, where all bytes are formatted the same 
       way.
         
         -- The codec interval is determined by:      
              .codec_interval_begin
              .codec_interval_size
         
         -- The byte formatting range is determined by its index.
              .byte_format_range_index

         -- In order to know where to start, the unicode offset that corresponds 
            to the codec interval must be specified:
              .codec_interval_begin_unicode

       Figure:

              Source Codec
                              ci_begin       
                              |
              ................[xxxxxxxxxxxxxxx]................
                              |--- ci_size -->|


              belongs to


              Unicode    |<----          byte formatting range         ---->|
                                                                             
                         |                           |--- ci_size-->|       |
              ...........[+++++++++++++++++++++++++++|xxxxxxxxxxxxxx|++++++][
                                                     |
                                                     ci_begin_unicode
                                                      

       The codec interval always lies inside a single utf8 range.
    """
    def __init__(self, RangeIndex, CI_Begin_in_Unicode, CI_Begin, CI_Size=-1):
        self.byte_format_range_index      = RangeIndex
        self.codec_interval_begin         = CI_Begin
        self.codec_interval_size          = CI_Size
        self.codec_interval_begin_unicode = CI_Begin_in_Unicode

    def __repr__(self):
        return "[%i] at %08X: Codec Interval [%X,%X)" % \
               (self.byte_format_range_index,
                self.codec_interval_begin_unicode,
                self.codec_interval_begin,
                self.codec_interval_begin + self.codec_interval_size)

