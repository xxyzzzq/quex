#! /usr/bin/env python
import sys
import os
import StringIO
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.utf8            as utf8

if "--hwut-info" in sys.argv:
    print "UTF8: Map UTF8 String To Unicode Values"
    sys.exit(0)
    
# the unequal sign from the utf-8 manpage
txt = chr(0xE2) + chr(0x89) + chr(0xA0)
# unicode character (C) from the utf-8 man-page
txt += chr(0xC2) + chr(0xA9)
# unicode character 'Lam' in the arabic code page
txt += chr(0xd9) + chr(0x84) 
cstr = StringIO.StringIO(txt)

print "unequal-sign:   E2.89.A0 -> %x" % utf8.map_utf8_to_unicode(cstr)
print "copyright-sign: C2.A9    -> %x" % utf8.map_utf8_to_unicode(cstr)
print "arabic lam:     D9.84    -> %x" % utf8.map_utf8_to_unicode(cstr)
# print map(lambda x: "%x" % x, utf8.read(cstr,10000))

print "%x -> %s" % (0x2260, utf8.map_unicode_to_utf8(0x2260))
print "%x -> %s" % (0xA9,   utf8.map_unicode_to_utf8(0xA9))
print "%x -> %s" % (0x644,  utf8.map_unicode_to_utf8(0x644))


