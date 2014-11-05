#! /usr/bin/env python
#
# PURPOSE:
# 
# Test the generation of a comparision sequence to map from intervals
# to targets. Class under test is 'ComparisonSequence'.
#
# This tests sets up transition maps of different sizes. By the setting
# of 'Setup.buffer_limit_code' the direction of the map implementation 
# is controlled. Since the buffer limit code is considered to appear very
# seldomly, it is always checked last.
#
# Optimization is considered implicitly. 
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import sys
import os
import random
sys.path.insert(0, os.environ["QUEX_PATH"])
from   copy import copy
                                                   
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.generator.state.transition_map.comparison_sequence import ComparisonSequence   
from   quex.engine.generator.languages.core import db
from   quex.engine.interval_handling        import Interval
from   quex.engine.analyzer.transition_map  import TransitionMap   
from   quex.blackboard                      import setup as Setup, \
                                                   Lng
from   collections import defaultdict

if "--hwut-info" in sys.argv:
    print "Code generation: Comparison Sequence;"
    print "CHOICES: C-2-fw, C-2-bw, C-3-fw, C-3-bw, C-4-fw, C-4-bw, C-5-fw, C-5-bw;"
    sys.exit()

if len(sys.argv) < 2: 
    print "Not enough arguments"
    exit()

Lang, N, Direction = sys.argv[1].split("-")

Setup.language_db = db[Lang]
N = int(N)

interval_begin = 0
def interval(Size):
    # NOTE: 'interval_begin=0' is reset at the end of test()
    global interval_begin
    result = Interval(interval_begin, interval_begin+Size)
    interval_begin += Size
    return result

def print_tm(tm):
    for interval, target in tm:
        print "    %-7s -> %s" % (interval, target)

def test(TM_plain):
    global interval_begin

    print "#" + "-" * 79
    tm = TransitionMap.from_iterable(
        (interval, long(target))
        for interval, target in TM_plain
    )
    print_tm(tm)
    node = ComparisonSequence(copy(tm))
    print "    ---"
    tm, default = ComparisonSequence.optimize(tm)
    print_tm(tm)
    print "    default:   %s" % repr(default)
    print "    ---"
    for element in node.implement():
        print "    %s" % element,

    interval_begin = 0

adr0 = dial_db.new_address()
adr1 = dial_db.new_address()

if Direction == "fw": Setup.buffer_limit_code = 1e37
else:                 Setup.buffer_limit_code = 0


if N == 2:
    for i in xrange(-1, 2):
        test([
            (interval(1 if i != 0 else 2), adr0),
            (interval(1 if i != 1 else 2), adr1),
        ])
    test([
        (interval(2), adr0),
        (interval(2), adr1),
    ])
elif N == 3:
    for i in xrange(-1, 3):
        test([
            (interval(1 if i != 0 else 2), adr0),
            (interval(1 if i != 1 else 2), adr1),
            (interval(1 if i != 2 else 2), adr0),
        ])
    for i in xrange(0, 3):
        test([
            (interval(1 if i == 0 else 2), adr0),
            (interval(1 if i == 1 else 2), adr1),
            (interval(1 if i == 2 else 2), adr0),
        ])
    test([
        (interval(2), adr0),
        (interval(2), adr1),
        (interval(2), adr0),
    ])
elif N == 4:
    for i in xrange(-1, 4):
        test([
            (interval(1 if i != 0 else 2), adr0),
            (interval(1 if i != 1 else 2), adr1),
            (interval(1 if i != 2 else 2), adr0),
            (interval(1 if i != 3 else 2), adr1),
        ])
    for i in xrange(0, 4):
        test([
            (interval(1 if i == 0 else 2), adr0),
            (interval(1 if i == 1 else 2), adr1),
            (interval(1 if i == 2 else 2), adr0),
            (interval(1 if i == 3 else 2), adr1),
        ])
    test([
        (interval(2), adr0),
        (interval(2), adr1),
        (interval(2), adr0),
        (interval(2), adr1),
    ])
elif N == 5:
    for i in xrange(-1, 4):
        test([
            (interval(1 if i != 0 else 2), adr0),
            (interval(1 if i != 1 else 2), adr1),
            (interval(1 if i != 2 else 2), adr0),
            (interval(1 if i != 3 else 2), adr1),
            (interval(1 if i != 4 else 2), adr0),
        ])
    for i in xrange(0, 4):
        test([
            (interval(1 if i == 0 else 2), adr0),
            (interval(1 if i == 1 else 2), adr1),
            (interval(1 if i == 2 else 2), adr0),
            (interval(1 if i == 3 else 2), adr1),
            (interval(1 if i == 4 else 2), adr0),
        ])
    test([
        (interval(2), adr0),
        (interval(2), adr1),
        (interval(2), adr0),
        (interval(2), adr1),
        (interval(2), adr0),
    ])
