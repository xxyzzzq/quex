#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling       import Interval
import quex.engine.analyzer.transition_map as     transition_map_tools
from   quex.engine.analyzer.transition_map import TransitionMap
from   copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Transition Map Tools: TransitionMap.izip;"
    sys.exit()

def test(Name, TM_A, TM_B):
    tm_a = TransitionMap.from_iterable((Interval(x[0], x[1]), x[2]) for x in TM_A)
    tm_b = TransitionMap.from_iterable((Interval(x[0], x[1]), x[2]) for x in TM_B)
    print "____________________________________________________________________"
    print
    print "Transition Map A:"
    print tm_a.get_string("dec", IntervalF=False),
    print
    print "Transition Map B:"
    print tm_b.get_string("dec", IntervalF=False),
    print
    print "Result:"
    for begin, end, a, b in TransitionMap.izip(tm_a, tm_b):
        x = "%i" % begin if begin != -sys.maxint else "-oo"
        y = "%i" % end   if end   != sys.maxint else "+oo"
        print "  [%3s:%3s)   %s  %s" % (x, y, a, b)
    print
    print "Result (switched):"
    for begin, end, a, b in TransitionMap.izip(tm_b, tm_a):
        x = "%i" % begin if begin != -sys.maxint else "-oo"
        y = "%i" % end   if end   != sys.maxint else "+oo"
        print "  [%3s:%3s)   %s  %s" % (x, y, a, b)

test("X", 
     [ (-sys.maxint, sys.maxint, "0") ], 
     [ (-sys.maxint, sys.maxint, "1") ])
test("X", 
     [ (-sys.maxint, 0, "0"), (0, sys.maxint, "1") ], 
     [ (-sys.maxint, sys.maxint, "2") ])
test("X", 
     [ (-sys.maxint, 0, "0"), (0, sys.maxint, "1") ], 
     [ (-sys.maxint, 0, "2"), (0, sys.maxint, "3") ]) 
test("X", 
     [ (-sys.maxint, 0, "0"), (0, sys.maxint, "1") ], 
     [ (-sys.maxint, 1, "2"), (1, sys.maxint, "3") ]) 
test("X", 
     [ (-sys.maxint, 0, "0"), (0, 10, "1"), (10, sys.maxint, "2") ], 
     [ (-sys.maxint, 1, "2"), (1, sys.maxint, "3") ]) 
test("X", 
     [ (-sys.maxint, 0, "0"), (0, 10, "1"), (10, sys.maxint, "2") ], 
     [ (-sys.maxint, 1, "3"), (1, 20, "4"), (20, sys.maxint, "5") ]) 
test("X", 
     [ (-sys.maxint, 0, "0"), (0, 10, "1"), (10, 30, "2"), (30, sys.maxint, "3") ], 
     [ (-sys.maxint, 1, "4"), (1, 20, "5"), (20, sys.maxint, "6") ]) 
test("X", 
     [ (-sys.maxint, 0, "0"), (0, 10, "1"), (10, 30, "2"), (30, 40, "3"), (40, sys.maxint, "4") ], 
     [ (-sys.maxint, 1, "5"), (1, 20, "6"), (20, sys.maxint, "7") ]) 

