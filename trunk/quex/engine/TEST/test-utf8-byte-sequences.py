#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.core_engine.utf8 import unicode_to_utf8, utf8_to_unicode
import codecs

if "--hwut-info" in sys.argv:
    print "UTF8: Conversion from and to byte sequences"
    sys.exit(0)

utf8c = codecs.getencoder("utf-8")
utf8d = codecs.getdecoder("utf-8")

def reference_utf8_encoder(UnicodeValue):
    return map(ord, utf8c(eval("u'\\U%08X'" % UnicodeValue))[0])

def reference_utf8_decoder(ByteSequence):
    return ord(utf8d("".join(map(chr, ByteSequence)))[0])

error_n = 0
def test(UC):
    global error_n
    correct = reference_utf8_encoder(UC)
    output  = unicode_to_utf8(UC)

    if correct != output:
        print "ERROR: unicode_to_utf8 with %06X" % UC
        print correct
        print output
        error_n += 1

    backward = utf8_to_unicode(correct)

    if backward != UC:
       print "ERROR: utf8_to_unicode with %06X" % UC
       error_n += 1

if False:
    # The lower plain is tested completely below
    test(0x42)
    test(0x43)
    test(0x7F)
    test(0x80)
    test(0x81)
    test(0x3FE)
    test(0x3FF)
    test(0x400)
    test(0x7FF)
    test(0x800)
    test(0x801)
    test(0x1000)
    test(0x3FFE)
    test(0x3FFF)
    test(0x4000)
    test(0x4001)
    test(0xFFFE)
    test(0xFFFF)
test(0x10000)
test(0x10001)
test(0x10FFF)
test(0x3FFFE)
test(0x3FFFF)
test(0x40000)
test(0x10FFFF)
test(0x10FFFE)

# Check the whole lower plain
for i in range(0x10000):
    test(i)

# Check the upper plain around critical points
cursor = [ 1, 0, 0 ]
value  = cursor[0] * 0x3F + cursor[1] * 0xFFF + cursor[2] * 0x3FFFF
while value < 0x10FFFF:
    test(value - 1)
    test(value)
    test(value + 1)
    cursor[0] += 1
    if cursor[0] * 0x3F >= 0xFFF: 
        cursor[0] = 0
        cursor[1] += 1
        if cursor[1] * 0xFFF > 0x3FFFF:
            cursor[1] = 0
            cursor[2] += 1
            if cursor[2] > 0x10FFFF:
                break
    value  = cursor[0] * 0x3F + cursor[1] * 0xFFF + cursor[2] * 0x3FFFF

print "ERROR COUNT:", error_n
