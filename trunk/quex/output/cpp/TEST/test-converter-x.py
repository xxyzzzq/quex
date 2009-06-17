#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
import quex.output.cpp.codec_converter_helper as codec_converter_helper

if "--hwut-info" in sys.argv:
    print "Converter: Determine UTF-8 Range Map for Codec"
    print "CHOICES:   1, 2, 3;"

def test(Msg, ConversionInfoList):
    print
    print "(*) " + Msg
    print 
    conversion_info = []
    for x in ConversionInfoList:
        info = codec_converter_helper.UTF8_ConversionInfo(x[0], x[1], x[2], x[3])
        print "    " + repr(info)
        conversion_info.append(info)
    print
    print codec_converter_helper.get_converter_to_utf8(conversion_info)


if "1" in sys.argv:
    #             RangeIndex  CI_Begin_in_Unicode  CI_Begin   CI_Size
    ConvInfo = [ [0,          0x00000,             0x1000000, 20]] 
    test("Single Interval A", ConvInfo)
    ConvInfo = [ [1,          0x00080,             0x1000000, 20]] 
    test("Single Interval B", ConvInfo)
    ConvInfo = [ [2,          0x00800,             0x1000000, 20]] 
    test("Single Interval C", ConvInfo)
    ConvInfo = [ [3,          0x10000,             0x1000000, 20]] 
    test("Single Interval E", ConvInfo)

elif "2" in sys.argv:
    #             RangeIndex  CI_Begin_in_Unicode  CI_Begin   CI_Size
    ConvInfo = [ [0,          0,                   0x100000,  0x10], 
                 [1,          0x80,                0x200000,  0x10],
                 [2,          0x800,               0x300000,  0x10],
                 [3,          0x10000,             0x400000,  0x10] ]
    test("4 Intervals", ConvInfo)

elif "3" in sys.argv:
    TrafoInfo = [ [0,       0x81,     0x1000000], 
                  [0x81,    0x801,    0x2000081], 
                  [0x801,   0x10001,  0x3000801], 
                  [0x10001, 0x200001, 0x4010001] ]
    ConvInfo = codec_converter_helper.get_utf8_conversion_table(TrafoInfo)
    ConvInfo = map(lambda x: [x.utf8_range_index, 
                              x.codec_interval_begin_unicode, 
                              x.codec_interval_begin,
                              x.codec_interval_size], ConvInfo)
    test("Intervals over borders (all)", ConvInfo)

