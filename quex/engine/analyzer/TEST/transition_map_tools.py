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
    print "CHOICES: Normal, Apart, AbsorbA, AbsorbB, AbsorbC;"
    sys.exit()

def show(TM):
    print transition_map_tools.get_string(TM, Option="dec")

def test(TM, Character, Target="<X>"):
    tm = deepcopy(TM)
    print "____________________________________________________________________"
    print "   len(TM) = %i; Insert at %i;" % (len(TM), Character)
    transition_map_tools.set(tm, Character, Target)
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

elif "Apart" in sys.argv:
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

elif "AbsorbA" in sys.argv:
    two = [(Interval(14, 15), "1"), (Interval(15, 20), "2")]

    test(two, 14, "1")
    test(two, 15, "1")
    test(two, 16, "1")
    test(two, 17, "1")

    test(two, 14, "2")
    test(two, 15, "2")
    test(two, 16, "2")
    test(two, 17, "2")

elif "AbsorbB" in sys.argv:
    two = [(Interval(10, 15), "1"), (Interval(15, 16), "2")]

    test(two, 12, "1")
    test(two, 13, "1")
    test(two, 14, "1")
    test(two, 15, "1")

    test(two, 12, "2")
    test(two, 13, "2")
    test(two, 14, "2")
    test(two, 15, "2")


elif "AbsorbC" in sys.argv:
    two = [(Interval(14, 15), "1"), (Interval(15, 16), "2")]

    test(two, 14, "1")
    test(two, 15, "1")

    test(two, 14, "2")
    test(two, 15, "2")

    three = [(Interval(14, 15), "1"), (Interval(15, 16), "2"), (Interval(16, 17), "3")]
    test(three, 14, "1")
    test(three, 15, "1")
    test(three, 16, "1")

    test(three, 14, "2")
    test(three, 15, "2")
    test(three, 16, "2")

    test(three, 14, "3")
    test(three, 15, "3")
    test(three, 16, "3")

    three_b = [(Interval(10, 15), "1"), (Interval(15, 16), "2"), (Interval(16, 20), "3")]

    test(three_b, 14, "1")
    test(three_b, 15, "1")
    test(three_b, 16, "1")

    test(three_b, 14, "2")
    test(three_b, 15, "2")
    test(three_b, 16, "2")

    test(three_b, 14, "3")
    test(three_b, 15, "3")
    test(three_b, 16, "3")

