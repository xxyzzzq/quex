#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.misc.interval_handling import Interval

if "--hwut-info" in sys.argv:
    print "NumberSet: Interval comparison"
    print "CHOICES: normal, special"
    sys.exit(0)

def test(A0, A1, B0, B1):
    print "------------------------------------------------"
    A = Interval(A0, A1)
    B = Interval(B0, B1)
    print "%s <  %s : %s" % (repr(A), repr(B), A <  B)
    print "%s <= %s : %s" % (repr(A), repr(B), A <= B)
    print "%s == %s : %s" % (repr(A), repr(B), A == B)
    print "%s != %s : %s" % (repr(A), repr(B), A != B)
    print "%s >= %s : %s" % (repr(A), repr(B), A >= B)
    print "%s >  %s : %s" % (repr(A), repr(B), A >  B)

if "normal" in sys.argv:
    test(10, 30, 40, 70)
    test(40, 50, 40, 70)
    test(40, 70, 40, 70)
    test(50, 70, 40, 70)

    test(40, 70, 10, 30)
    test(40, 70, 40, 50)
    test(40, 70, 40, 70)
    test(40, 70, 50, 70)

elif "special" in sys.argv:
    test(10, 30, 40, 70)
    test(41, 50, 40, 70)
    test(40, 71, 40, 70)
    test(50, 69, 40, 70)

    test(40, 70, 10, 30)
    test(40, 70, 41, 50)
    test(40, 70, 40, 71)
    test(40, 70, 50, 69)
