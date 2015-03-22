#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.misc.utf8  as utf8
import quex.engine.misc.utf16 as utf16

def byte_4_split(Value):
    return "".join(map(chr, [Value & 0xFF, (Value >> 8) & 0xFF, (Value >> 16) & 0xFF, Value >> 24]))

def word_4_split(Values):
    result = ""
    for value in Values:
        byte0 = value & 0xFF
        byte1 = value >> 8
        assert value & 0xFFFF0000 == 0, "Value = %08X" % value
        result += chr(byte0) + chr(byte1)
    return result

# (1) Critical Borders for UTF8: 
#     0x80, 0x800, 0x10000, 0x10ffff (last code element)
# (2) Critical Borders for UTF16: 
#     0xD800, 0xE000
unicode_character_list =   range(0x01, 0x7F)            \
                         + range(0x800, 0x800 +10)      \
                         + range(0x10000, 0x10000 + 10) 

utf8_list    = ""
utf16_list   = ""
unicode_list = ""
for char in unicode_character_list:
    utf8_list    += utf8.map_unicode_to_utf8(char)
    utf16_list   += word_4_split(utf16.unicode_to_utf16(char))
    unicode_list += byte_4_split(char)

fh = open("example/utf8.txt", "wb")
fh.write(utf8_list)
fh.close()
fh = open("example/utf16le.txt", "wb")
fh.write("\xff\xfe" + utf16_list) # BOM: Little Endian
fh.close()
fh = open("example/ucs4le.txt", "wb")
fh.write(unicode_list)
fh.close()
