#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.misc.utf16 import unicode_to_utf16, utf16_to_unicode
import codecs

if "--hwut-info" in sys.argv:
    print "UTF16: Conversion from and to byte sequences"
    sys.exit(0)

utf16c = codecs.getencoder("utf-16be")
utf16d = codecs.getdecoder("utf-16be")

def reference_utf16_encoder(UnicodeValue):
    byte_seq = map(ord, utf16c(eval("u'\\U%08X'" % UnicodeValue))[0])
    if UnicodeValue >= 0x10000:
        word_seq = [ (byte_seq[0] << 8) + byte_seq[1], (byte_seq[2] << 8) + byte_seq[3] ]
    else:
        word_seq = [ (byte_seq[0] << 8) + byte_seq[1] ]
    return word_seq

error_n = 0
def test(UC):
    global error_n
    correct = reference_utf16_encoder(UC)
    output  = unicode_to_utf16(UC)

    if correct != output:
        print "ERROR: unicode_to_utf16 with %06X" % UC
        print correct
        print output
        print correct[0] - output[0]
        error_n += 1

    backward = utf16_to_unicode(correct)

    if backward != UC:
        print "ERROR: utf16_to_unicode with %06X" % UC
        error_n += 1

# Conversions in the lower plain a trivial
test(0x0)
test(0x1)
test(0xFFFC)
test(0xFFFD)
test(0xFFFE)
test(0xFFFF)
test(0x10000)
test(0x10001)

# Check the upper plain around critical points
cursor = [ 1, 0 ]
value  = 0x10000 + cursor[0] * 0x3F + cursor[1] * 0xFFF
while value < 0x10FFFF:
    test(value - 1)
    test(value)
    test(value + 1)
    cursor[0] += 1
    if cursor[0] * 0x3F >= 0xFFF: 
        cursor[0] = 0
        cursor[1] += 5
    value  = cursor[0] * 0x3F + cursor[1] * 0xFFF

print "ERROR COUNT:", error_n
