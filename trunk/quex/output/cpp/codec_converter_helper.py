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

utf8_converter_function_txt = \
"""
/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: Parts of the following have been derived from segments of the
 *                  utf8 conversion library of Alexey Vatchenko <av@bsdua.org>.    
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */

#ifndef __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_$$CODEC$$__
#define __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_$$CODEC$$__

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

#if ! defined(__QUEX_SETTING_PLAIN_C)
#   include <stdexcept>
namespace quex { 
#endif
QUEX_INLINE uint8_t*
Quex_$$CODEC$$_to_utf8(QUEX_TYPE_CHARACTER input, uint8_t* output)
{
$$CONST$$
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

$$BODY$$
    __quex_assert(p - output < (ptrdiff_t)7);
    __quex_assert(p > output);
    return p;

#   undef QUEX_BYTE_0 
#   undef QUEX_BYTE_1 
#   undef QUEX_BYTE_2 
#   undef QUEX_BYTE_3 
}

QUEX_INLINE uint8_t*
Quex_$$CODEC$$_to_utf8_string(QUEX_TYPE_CHARACTER* Source, size_t SourceSize, uint8_t *Drain, size_t DrainSize)
{
    QUEX_TYPE_CHARACTER *source_iterator, *source_end;
    uint8_t                *drain_iterator, *drain_end;

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

#if ! defined(__QUEX_SETTING_PLAIN_C)
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


} // namespace quex
#endif

#endif /* __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_$$CODEC$$__ */

"""

def do():
    if Setup.engine_character_encoding == "": return

    assert Setup.engine_character_encoding_transformation_info != None

    txt = write(Setup.engine_character_encoding_transformation_info, 
                Setup.engine_character_encoding)

    file_name = __prepare_file_name("-converter-%s" % Setup.engine_character_encoding)
    write_safely_and_close(file_name, txt) 

def write(TrafoInfo, CodecName):
    """
    PURPOSE: Writes converters for conversion towards Unicode (wchar_t) and utf8.
    """
    conversion_table = utf8_conversion_table_get(TrafoInfo)
    function_body    = utf8_converter_get(conversion_table)
    codec_name       = make_safe_identifier(CodecName)

    # Provide only the constant which are necessary

    return blue_print(utf8_converter_function_txt, 
                      [["$$CODEC$$", CodecName],
                       ["$$CONST$$", utf8_byte_constants_get(conversion_table)],
                       ["$$BODY$$",  function_body]])

class UTF8_ConversionInfo:
    """A given interval in the codec corresponds to a certain UTF-8 Range.
         -- The interval is determined by: Begin, Size.
         -- The UTF-8 range is determined by its index.
         -- The offset from the start of the utf8 range is also specified.
            It corresponds to the start of the codec interval. 

       Example:
              range index:   3                                        4
                             |                  |-- CI_Size-->|       |
                          ...[++++++++++++++++++|xxxxxxxxxxxxx|++++++][
                             |---RangeOffset--->|
                             0x10000

       The codec interval always lies inside a single utf8 range.
    """
    def __init__(self, RangeIndex, CI_Begin_in_Unicode, CI_Begin, CI_Size=-1):
        self.utf8_range_index             = RangeIndex
        self.codec_interval_begin         = CI_Begin
        self.codec_interval_size          = CI_Size
        self.codec_interval_begin_unicode = CI_Begin_in_Unicode

    def __repr__(self):
        return "[%i] at %08X: Codec Interval [%X,%X)" % \
               (self.utf8_range_index,
                self.codec_interval_begin_unicode,
                self.codec_interval_begin,
                self.codec_interval_begin + self.codec_interval_size)

def utf8_byte_constants_get(ConvTable):
    unique_range_index_list = []
    for info in ConvTable:
        if info.utf8_range_index not in unique_range_index_list:
            unique_range_index_list.append(info.utf8_range_index)
    unique_range_index_list.sort()

    db = { 2: 0xc0, 3: 0xe0, 4: 0xf0, 5: 0xf8, 6: 0xfc }
    txt = ""
    if unique_range_index_list[-1] != 0:
        txt += "    const int NEXT = 0x80;\n"
    for index in unique_range_index_list:
        if index > 0:
            txt += "    const int LEN%i = 0x%03X;\n" % (index + 1, db[index + 1])
    return txt

def utf8_conversion_table_get(TrafoInfo):
    """UTF8 covers the following regions with the corresponding numbers of bytes:
    
         0x00000000 - 0x0000007F: 1 byte  - 0xxxxxxx
         0x00000080 - 0x000007FF: 2 bytes - 110xxxxx 10xxxxxx
         0x00000800 - 0x0000FFFF: 3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
         0x00010000 - 0x001FFFFF: 4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
         0x00200000 - 0x03FFFFFF: 5 bytes ... 
         0x04000000 - 0x7FFFFFFF: 

       (1) Identify what regions in the trafo-info belong to what utf8-range.
       (2) Map those regions to target encoding regions.
       (3) For each region compute the conversion.
    """
    trafo_info  = copy(TrafoInfo)
    utf8_border = [ 0x0, 0x00000080, 0x00000800, 0x00010000, 0x00200000, 0x04000000, 0x80000000, sys.maxint] 
    L = len(utf8_border)

    # Sort transform info database according to target range
    info_list = []
    trafo_info.sort(lambda a, b: cmp(a[2], b[2]))
    for source_interval_begin, source_interval_end, target_interval_begin in trafo_info:

        # How does the target interval has to be split according to utf8-ranges?
        i = 0
        while source_interval_begin >= utf8_border[i]: 
            i += 1

        i -= 1
        ## print "##", i, source_interval_begin, utf8_border[i]
        # 'i' now stands on the first utf8_range that touches the source interval
        info = UTF8_ConversionInfo(i, source_interval_begin, target_interval_begin)

        # NOTE: size of target interval = size of source interval
        remaining_size = source_interval_end - source_interval_begin

        ## print "## %i, %x, %x" % (i, source_interval_begin, source_interval_end)
        while i != L - 1 and remaining_size != 0:
            remaining_utf8_range_size = utf8_border[i+1] - source_interval_begin
            info.codec_interval_size  = min(remaining_utf8_range_size, remaining_size)
            ## print i, "%X: %x, %x" % (utf8_border[i+1], remaining_utf8_range_size, remaining_size)
            info_list.append(info)

            source_interval_begin  = utf8_border[i+1] 
            target_interval_begin += info.codec_interval_size
            remaining_size        -= info.codec_interval_size
            i += 1
            info = UTF8_ConversionInfo(i, source_interval_begin, target_interval_begin)

        ## print "##", remaining_size
        if remaining_size != 0:
            info.codec_interval_size = remaining_size
            info_list.append(info)

    info_list.sort(lambda a, b: cmp(a.codec_interval_begin, b.codec_interval_begin))
    return info_list

def unicode_range_conversion_get(Info):
    assert isinstance(Info, UTF8_ConversionInfo)

    # Conversion to Unicode
    return "unicode = 0x%06X + (input - 0x%06X);\n" % \
           (Info.codec_interval_begin_unicode, Info.codec_interval_begin)

def utf8_byte_formatter_get(RangeIndex):
    # Byte Split
    txt = {
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

    return txt  

def utf8_converter_get(ConversionTable):
    """Creates code for a conversion to utf8 according to the ConversionTable.
       The conversion table has been created by function utf8_conversion_table_get().
    """
    # Make sure that the conversion table is sorted
    ConversionTable.sort(lambda a, b: cmp(a.codec_interval_begin, b.codec_interval_begin))

    def __same_utf8_range(ConvInfoList):
        """RETURNS: >= 0   the commond utf8 range index.
                    == -1  not all infos belong to the same utf8 range.
        """
        range_i = ConvInfoList[0].utf8_range_index
        for info in ConvInfoList[1:]:
            if info.utf8_range_index != range_i: return -1
        return ConvInfoList[0].utf8_range_index

    # Implement a binary bracketing of conversion domains
    def __bracket(conversion_list, CallerRangeIndex):
        txt = ""
        L = len(conversion_list)
        if   L == 1:
            txt += unicode_range_conversion_get(conversion_list[0])
            # The caller does have to implement an 'encoder
            if CallerRangeIndex != conversion_list[0].utf8_range_index:
                txt += utf8_byte_formatter_get(conversion_list[0].utf8_range_index)
        else:
            # Determine wether all sub-ranges belong to the same utf8-range
            range_index = __same_utf8_range(conversion_list)

            # Bracket interval in the middle
            mid_index = int(float(L)/2)
            Middle    = "0x%06X" % conversion_list[mid_index].codec_interval_begin
            txt += LanguageDB["$if <"](Middle) 
            if range_index != -1: 
                txt += __bracket(conversion_list[:mid_index], range_index)
                txt += LanguageDB["$endif-else"] + "\n"   
                txt += __bracket(conversion_list[mid_index:], range_index)
                txt += LanguageDB["$end-else"]
                if CallerRangeIndex != range_index:
                    txt += utf8_byte_formatter_get(range_index)
            else:
                txt += __bracket(conversion_list[:mid_index], range_index)
                txt += LanguageDB["$endif-else"] + "\n"   
                txt += __bracket(conversion_list[mid_index:], range_index)
                txt += LanguageDB["$end-else"]

        return "    " + txt[:-1].replace("\n", "\n    ") + "\n"

    range_index = __same_utf8_range(ConversionTable)
    txt = __bracket(ConversionTable, range_index)
    if range_index != -1: 
        formatter_txt = utf8_byte_formatter_get(range_index)
        txt += "    " + formatter_txt[:-1].replace("\n", "\n    ") + "\n"
    return txt
