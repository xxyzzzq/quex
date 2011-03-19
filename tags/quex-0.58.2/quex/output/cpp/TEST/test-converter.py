#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
import quex.output.cpp.codec_converter_helper    as codec_converter_helper
import quex.core_engine.generator.languages.core as languages
import quex.input.setup

quex.input.setup.setup.language_db = languages.db["C++"]

if "--hwut-info" in sys.argv:
    print "Converter: Determine UTF-8 Range Map for Codec"
    print "CHOICES:   1, 2, 3, 4;"

def test(Msg, TrafoInfo):
    print
    print "(*) " + Msg
    print 
    for record in TrafoInfo:
        print "    [%06X,%06X) --> %06X" % (record[0], record[1], record[2])
    print
    for record in codec_converter_helper.ConverterWriterUTF8().get_conversion_table(TrafoInfo):
        print "    " + repr(record)

if "1" in sys.argv:
    TrafoInfo = [ [0,       0x200000, 0x1000000]] 
    test("One target interval that covers all", TrafoInfo)

elif "2" in sys.argv:
    TrafoInfo = [ [0,       0x80,     0x1000000], 
                  [0x80,    0x800,    0x2000080],
                  [0x800,   0x10000,  0x3000800],
                  [0x10000, 0x200000, 0x4010000] ]
    test("Map 1:1 to utf8", TrafoInfo)

elif "3" in sys.argv:
    TrafoInfo = [ [0,       0x81,     0x1000000] ]
    test("Intervals over borders 1", TrafoInfo)
    TrafoInfo = [ [0x81,    0x801,    0x2000081] ]
    test("Intervals over borders 2", TrafoInfo)
    TrafoInfo = [ [0x801,   0x10001,  0x3000801] ]
    test("Intervals over borders 3", TrafoInfo)
    TrafoInfo = [ [0x10001, 0x200001, 0x4010001] ]
    test("Intervals over borders 4", TrafoInfo)
    TrafoInfo = [ [0,       0x81,     0x1000000], 
                  [0x81,    0x801,    0x2000081], 
                  [0x801,   0x10001,  0x3000801], 
                  [0x10001, 0x200001, 0x4010001] ]
    test("Intervals over borders (all)", TrafoInfo)

elif "4" in sys.argv:
    TrafoInfo = [ [0x7F,    0x81,     0x100007f] ]
    test("Intervals over borders 1", TrafoInfo)
    TrafoInfo = [ [0x7FF,   0x801,    0x20007ff] ]
    test("Intervals over borders 2", TrafoInfo)
    TrafoInfo = [ [0xFFFF,  0x10001,  0x300ffff] ]
    test("Intervals over borders 3", TrafoInfo)
    TrafoInfo = [ [0x1FFFF, 0x200001, 0x401ffff] ]
    test("Intervals over borders 4", TrafoInfo)

    TrafoInfo = [ [0x7F,    0x81,     0x100007f],
                  [0x7FF,   0x801,    0x20007ff],
                  [0xFFFF,  0x10001,  0x300ffff],
                  [0x1FFFF, 0x200001, 0x401ffff] ]
    test("Intervals over borders (all)", TrafoInfo)
