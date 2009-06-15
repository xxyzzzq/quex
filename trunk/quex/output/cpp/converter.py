import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from copy import copy
from quex.core_engine.interval_handling import Interval
from   quex.input.setup import setup as Setup

LanguageDB = Setup.language_db

utf8_converter_function_txt = \
"""
char*
Quex_converter_$$CODEC$$_to_utf8(QUEX_TYPE_CHARACTER* input, char* output)
{
    const char NEXT	= 0x80;
    const char LEN2	= 0xc0;
    const char LEN3	= 0xe0;
    const char LEN4	= 0xf0;
    const char LEN5	= 0xf8;
    const char LEN6	= 0xfc;

#   if defined(__QUEX_OPTION_LITTLE_ENDIAN)
#   define QUEX_BYTE_0  (((char*)unicode)[3])
#   define QUEX_BYTE_1  (((char*)unicode)[2])
#   define QUEX_BYTE_2  (((char*)unicode)[1])
#   define QUEX_BYTE_3  (((char*)unicode)[0])
#   else
#   define QUEX_BYTE_0  (((char*)unicode)[0])
#   define QUEX_BYTE_1  (((char*)unicode)[1])
#   define QUEX_BYTE_2  (((char*)unicode)[2])
#   define QUEX_BYTE_3  (((char*)unicode)[3])
#   endif

$$BODY$$
    return p;
}
"""
def write(TrafoInfo, CodecName):
    """
    PURPOSE: Writes converters for conversion towards Unicode (wchar_t) and utf8.
    """
    conversion_table = get_utf8_conversion_table(TrafoInfo)
    function_body    = get_converter_to_utf8(conversion_table)

    return blue_print(utf8_converter_function_txt, 
                      [["$$CODEC$$", codec_name],
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

def get_utf8_conversion_table(TrafoInfo):
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

def implement_utf8_conversion(Info, Depth):
    assert isinstance(Info, UTF8_ConversionInfo)

    # Conversion to Unicode
    txt = "unicode = 0x%06X + (CodecCode - 0x%06X);\n" % \
           (Info.codec_interval_begin_unicode, Info.codec_interval_begin)

    # Byte Split
    txt += {
            0: 
            "*p = BYTE_0; ++p;\n",
            1:
            "*(p++) = LEN2 | (BYTE_0 >> 6) | ((BYTE_1 & 0x07) << 2);\n" + \
            "*(p++) = NEXT | BYTE_0 & 0x3f;\n",

            2:
            "*(p++) = LEN3 | ((BYTE_1 & 0xf0) >> 4);\n" + \
            "*(p++) = NEXT | (BYTE_0 >> 6) | ((BYTE_1 & 0x0f) << 2);\n" + \
            "*(p++) = NEXT | BYTE_0 & 0x3f;\n",

            3:
            "*(p++) = LEN4 | ((BYTE_2 & 0x1f) >> 2);\n" + \
            "*(p++) = NEXT | ((BYTE_1 & 0xf0) >> 4) | ((BYTE_2 & 0x03) << 4);\n" + \
            "*(p++) = NEXT | (BYTE_0 >> 6) | ((BYTE_1 & 0x0f) << 2);\n" + \
            "*(p++) = NEXT | BYTE_0 & 0x3f;\n", 

            4:
            "*(p++) = LEN5 | BYTE_3 & 0x03;\n" + \
            "*(p++) = NEXT | (BYTE_2 >> 2);\n" + \
            "*(p++) = NEXT | ((BYTE_1 & 0xf0) >> 4) | ((BYTE_2 & 0x03) << 4);\n" + \
            "*(p++) = NEXT | (BYTE_0 >> 6) | ((BYTE_1 & 0x0f) << 2);\n" + \
            "*(p++) = NEXT | BYTE_0 & 0x3f;\n",

            5:
            "*(p++) = LEN6 | ((BYTE_3 & 0x40) >> 6);\n" + \
            "*(p++) = NEXT | BYTE_3 & 0x3f;\n" + \
            "*(p++) = NEXT | (BYTE_2 >> 2);\n" + \
            "*(p++) = NEXT | (BYTE_1 >> 4) | ((BYTE_2 & 0x03) << 4);\n" + \
            "*(p++) = NEXT | (BYTE_0 >> 6) | ((BYTE_1 & 0x0f) << 2);\n" + \
            "*(p++) = NEXT | BYTE_0 & 0x3f;\n",

    }[Info.utf8_range_index] 

    return "    " + txt[:-1].replace("\n", "\n    ") + "\n"

def get_converter_to_utf8(ConversionTable):
    """Creates code for a conversion to utf8 according to the ConversionTable.
       The conversion table has been created by function get_utf8_conversion_table().
    """
    # Make sure that the conversion table is sorted
    ConversionTable.sort(lambda a, b: cmp(a.codec_interval_begin, b.codec_interval_begin))

    # Implement a binary bracketing of conversion domains
    def __bracket(conversion_list, Depth):
        txt = ""
        L = len(conversion_list)
        if   L == 1:
            txt += implement_utf8_conversion(conversion_list[0], Depth)
        elif L == 2:
            Middle = "0x%06X" % conversion_list[1].codec_interval_begin
            txt += LanguageDB["$if <"](Middle) + implement_utf8_conversion(conversion_list[0], Depth)
            txt += LanguageDB["$else"] + "\n"  + implement_utf8_conversion(conversion_list[1], Depth)
            txt += LanguageDB["$end-else"]
        else:
            mid_index = int(float(L)/2)
            Middle    = "0x%06X" % conversion_list[mid_index].codec_interval_begin
            txt += LanguageDB["$if <"](Middle) + __bracket(conversion_list[:mid_index], Depth+1)
            txt += LanguageDB["$else"] + "\n"  + __bracket(conversion_list[mid_index:], Depth+1)
            txt += LanguageDB["$end-else"]
        return "    " + txt[:-1].replace("\n", "\n    ") + "\n"

    return __bracket(ConversionTable, 0)
