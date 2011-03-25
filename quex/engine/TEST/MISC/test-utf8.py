#! /usr/bin/env python
import sys
sys.path.append("../")
from quex.engine.interval_handling import Interval

import utf8
import StringIO

# the unequal sign from the utf-8 manpage
txt = chr(0xE2) + chr(0x89) + chr(0xA0)

# unicode character (C) from the utf-8 man-page
txt += chr(0xC2) + chr(0xA9)

cstr = StringIO.StringIO(txt)

print "E2.89.A0 -> %x" % utf8.read_one(cstr)
print "C2.A9    -> %x" % utf8.read_one(cstr)

print "%x -> %s" % (0x2260, map(lambda x: "%x" % x, utf8.map_unicode_to_utf8(0x2260)))
print "%x -> %s" % (0xA9,   map(lambda x: "%x" % x, utf8.map_unicode_to_utf8(0xA9)))

txt = open("test-utf8.txt").read()[1:]
cstr = StringIO.StringIO(txt)

# print map(lambda x: "%x" % x, utf8.read(cstr,10000))
