#! /usr/bin/env python
from   copy import deepcopy
from   random import random

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from   quex.engine.misc.interval_handling import Interval, NumberSet
from   quex.engine.state_machine.transformation.table import EncodingTrafoByTable


if "--hwut-info" in sys.argv:
    print "NumberSet: Transform Codec cp037;"
    print "CHOICES:   1, all, some;"
    sys.exit(0)

# The codec cp037 is so wonderful, because it shuffles all unicode
# code points nicely.

trafo_cp037 = EncodingTrafoByTable("cp037")

if "1" in sys.argv:
    def test(UC):
        global trafo_cp037
        x = NumberSet(UC)
        y = x.clone()
        x.transform(trafo_cp037)
        x.assert_consistency()
        print "0x%02X --> 0x%s" % (UC, x.get_string(Option="hex"))

    for letter in xrange(-2, 258):
        test(letter)

elif "all" in sys.argv:

    x = NumberSet(Interval(0, 0x100))
    y = x.clone()
    x.transform(trafo_cp037)
    x.assert_consistency()
    print "0x%s --> 0x%s" % (y, x.get_string(Option="hex"))

elif "some" in sys.argv:
    x = NumberSet(Interval(0, 0x32))
    y = x.clone()
    x.transform(trafo_cp037)
    x.assert_consistency()
    print "0x%s --> 0x%s" % (y, x.get_string(Option="hex"))

    x = NumberSet(Interval(0x42, 0x80))
    y = x.clone()
    x.transform(trafo_cp037)
    x.assert_consistency()
    print "0x%s --> 0x%s" % (y, x.get_string(Option="hex"))

    x = NumberSet(Interval(0xA0, 0xFF))
    y = x.clone()
    x.transform(trafo_cp037)
    x.assert_consistency()
    print "0x%s --> 0x%s" % (y, x.get_string(Option="hex"))
