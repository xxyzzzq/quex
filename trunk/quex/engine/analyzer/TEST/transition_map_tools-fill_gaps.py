#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling       import Interval
from   quex.engine.analyzer.transition_map import TransitionMap
from   copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Transition Map Tools: fill_gaps;"
    print "CHOICES: 1, 2-same, 2-diff, 3-same, 3-diff;"
    sys.exit()


def show(TM):
    txt = TM.get_string(Option="dec")
    txt = txt.replace("%s" % -sys.maxint, "-oo")
    txt = txt.replace("%s" % (sys.maxint-1), "oo")
    print txt

def test(TM, Target="X"):
    tm = TransitionMap([ (Interval(x[0], x[1]), y) for x, y in TM ])
    print "____________________________________________________________________"
    print "BEFORE:"
    show(tm)
    tm.fill_gaps(Target)
    tm.assert_adjacency(ChangeF=True)
    print "AFTER:"
    show(tm)

#test([((0, 1),           "1"), ((10, 11),        "2")], "1")
#sys.exit()

if "1" in sys.argv:
    test([((0, 1),                    "1")])
    test([((-sys.maxint, 1),          "1")])
    test([((0, sys.maxint),           "1")])
    test([((-sys.maxint, sys.maxint), "1")])

    print "# Required: Smoothing ______________________________________________"
    test([((0, 1),                    "1")], "1")
    test([((-sys.maxint, 1),          "1")], "1")
    test([((0, sys.maxint),           "1")], "1")
    test([((-sys.maxint, sys.maxint), "1")], "1")

elif "2-same" in sys.argv:

    test([((0, 1),           "1"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((1, 2),          "1")])
    test([((-sys.maxint, 1), "1"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((1, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((1, sys.maxint), "1")])

    print "# Required: Smoothing ______________________________________________"
    test([((0, 1),           "1"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((1, 2),          "1")], "1")
    test([((-sys.maxint, 1), "1"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((1, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((1, sys.maxint), "1")], "1")

elif "2-diff" in sys.argv:

    test([((0, 1),           "1"), ((10, 11),        "2")])
    test([((0, 1),           "1"), ((1, 2),          "2")])
    test([((-sys.maxint, 1), "1"), ((10, 11),        "2")])
    test([((0, 1),           "1"), ((1, sys.maxint), "2")])
    test([((-sys.maxint, 1), "1"), ((1, sys.maxint), "2")])

    print "# Required: Smoothing ______________________________________________"
    test([((0, 1),           "1"), ((10, 11),        "2")], "1")
    test([((0, 1),           "1"), ((1, 2),          "2")], "1")
    test([((-sys.maxint, 1), "1"), ((10, 11),        "2")], "1")
    test([((0, 1),           "1"), ((1, sys.maxint), "2")], "1")
    test([((-sys.maxint, 1), "1"), ((1, sys.maxint), "2")], "1")

    test([((0, 1),           "1"), ((10, 11),        "2")], "2")
    test([((0, 1),           "1"), ((1, 2),          "2")], "2")
    test([((-sys.maxint, 1), "1"), ((10, 11),        "2")], "2")
    test([((0, 1),           "1"), ((1, sys.maxint), "2")], "2")
    test([((-sys.maxint, 1), "1"), ((1, sys.maxint), "2")], "2")

elif "3-same" in sys.argv:

    test([((0, 1),           "1"), ((5, 6),          "1"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((1, 2),          "1"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((9, 10),         "1"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((1, 2),          "1"), ((2, 4),          "1")])

    test([((-sys.maxint, 1), "1"), ((5, 6),          "1"), ((10, 11),         "1")])
    test([((0, 1),           "1"), ((5, 6),          "1"), ((10, sys.maxint), "1")])

    test([((-sys.maxint, 1), "1"), ((5, 6),          "1"), ((10, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((1, 2),          "1"), ((10, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((9, 10),         "1"), ((10, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((1, 2),          "1"), ((2,  sys.maxint), "1")])

    print "# Required: Smoothing ______________________________________________"
    test([((0, 1),           "1"), ((5, 6),          "1"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((1, 2),          "1"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((9, 10),         "1"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((1, 2),          "1"), ((2, 4),          "1")], "1")

    test([((-sys.maxint, 1), "1"), ((5, 6),          "1"), ((10, 11),         "1")], "1")
    test([((0, 1),           "1"), ((5, 6),          "1"), ((10, sys.maxint), "1")], "1")

    test([((-sys.maxint, 1), "1"), ((5, 6),          "1"), ((10, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((1, 2),          "1"), ((10, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((9, 10),         "1"), ((10, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((1, 2),          "1"), ((2,  sys.maxint), "1")], "1")


elif "3-diff" in sys.argv:

    test([((0, 1),           "1"), ((5, 6),          "2"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((1, 2),          "2"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((9, 10),         "2"), ((10, 11),        "1")])
    test([((0, 1),           "1"), ((1, 2),          "2"), ((2, 4),          "1")])

    test([((-sys.maxint, 1), "1"), ((5, 6),          "2"), ((10, 11),         "1")])
    test([((0, 1),           "1"), ((5, 6),          "2"), ((10, sys.maxint), "1")])

    test([((-sys.maxint, 1), "1"), ((5, 6),          "2"), ((10, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((1, 2),          "2"), ((10, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((9, 10),         "2"), ((10, sys.maxint), "1")])
    test([((-sys.maxint, 1), "1"), ((1, 2),          "2"), ((2,  sys.maxint), "1")])

    print "# Required: Smoothing ______________________________________________"
    print "# --> 1"
    test([((0, 1),           "1"), ((5, 6),          "2"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((1, 2),          "2"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((9, 10),         "2"), ((10, 11),        "1")], "1")
    test([((0, 1),           "1"), ((1, 2),          "2"), ((2, 4),          "1")], "1")

    test([((-sys.maxint, 1), "1"), ((5, 6),          "2"), ((10, 11),         "1")], "1")
    test([((0, 1),           "1"), ((5, 6),          "2"), ((10, sys.maxint), "1")], "1")

    test([((-sys.maxint, 1), "1"), ((5, 6),          "2"), ((10, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((1, 2),          "2"), ((10, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((9, 10),         "2"), ((10, sys.maxint), "1")], "1")
    test([((-sys.maxint, 1), "1"), ((1, 2),          "2"), ((2,  sys.maxint), "1")], "1")

    print "# --> 2"
    test([((0, 1),           "1"), ((5, 6),          "2"), ((10, 11),        "1")], "2")
    test([((0, 1),           "1"), ((1, 2),          "2"), ((10, 11),        "1")], "2")
    test([((0, 1),           "1"), ((9, 10),         "2"), ((10, 11),        "1")], "2")
    test([((0, 1),           "1"), ((1, 2),          "2"), ((2, 4),          "1")], "2")

    test([((-sys.maxint, 1), "1"), ((5, 6),          "2"), ((10, 11),         "1")], "2")
    test([((0, 1),           "1"), ((5, 6),          "2"), ((10, sys.maxint), "1")], "2")

    test([((-sys.maxint, 1), "1"), ((5, 6),          "2"), ((10, sys.maxint), "1")], "2")
    test([((-sys.maxint, 1), "1"), ((1, 2),          "2"), ((10, sys.maxint), "1")], "2")
    test([((-sys.maxint, 1), "1"), ((9, 10),         "2"), ((10, sys.maxint), "1")], "2")
    test([((-sys.maxint, 1), "1"), ((1, 2),          "2"), ((2,  sys.maxint), "1")], "2")




