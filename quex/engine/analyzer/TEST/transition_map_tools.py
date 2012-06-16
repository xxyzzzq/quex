#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling       import Interval
import quex.engine.analyzer.transition_map as     transition_map_tools
from   copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Transition Map Tools: set;"
    print "CHOICES: Normal, Apart;"
    sys.exit()

def show(TM):
    if len(TM) == 0:
        print "<empty>"
        return
    L = max(len(repr(x[0])) for x in TM)
    for interval, target in TM:
        interval_str = repr(interval)
        print "   %s%s %s" % (interval_str, " " * (L - len(interval_str)), target)

def test(TM, Character):
    tm = deepcopy(TM)
    print "____________________________________________________________________"
    print "   len(TM) = %i; Insert at %i;" % (len(TM), Character)
    transition_map_tools.set(tm, Character, "<X>")
    show(tm)

if "Normal" in sys.argv:
    one = [(Interval(10, 15), "1")]
    two = [(Interval(10, 15), "1"), (Interval(15, 20), "2")]

    test(one, 10)
    test(one, 14)
    test(one, 12)
    test(two, 10)
    test(two, 14)
    test(two, 12)
    test(two, 15)
    test(two, 19)
    test(two, 17)

else:
    one   = [(Interval(14, 15), "1")]
    two_a = [(Interval(14, 15), "1"), (Interval(15, 16), "2")]
    two_b = [(Interval(10, 15), "1"), (Interval(15, 16), "2")]
    two_c = [(Interval(14, 15), "1"), (Interval(15, 20), "2")]

    test(one, 14)
    test(two_a, 14)
    test(two_a, 15)

    test(two_b, 10)
    test(two_b, 14)
    test(two_b, 12)
    test(two_b, 15)

    test(two_c, 14)
    test(two_c, 15)
    test(two_c, 19)
    test(two_c, 17)
