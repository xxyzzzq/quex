#! /usr/bin/env python
#
# PURPOSE:
# 
# Test the generation of a branch tables to map from intervals to targets. The
# Class under test is 'BranchTable'.
#
# This tests sets up transition maps of different sizes. 
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import sys
import os
import random
sys.path.insert(0, os.environ["QUEX_PATH"])
from   copy import copy
                                                   
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.generator.state.transition_map.branch_table import BranchTable   
from   quex.engine.generator.languages.core import db
from   quex.engine.interval_handling        import Interval
from   quex.engine.analyzer.transition_map  import TransitionMap   
from   quex.blackboard                      import setup as Setup, \
                                                   Lng
from   collections import defaultdict

if "--hwut-info" in sys.argv:
    print "Code generation: Branch Table (switch-case);"
    print "CHOICES: C-2, C-3, C-4, C-5;"
    sys.exit()

if len(sys.argv) < 2: 
    print "Not enough arguments"
    exit()

Lang, N = sys.argv[1].split("-")

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
        (interval, long(target)) for interval, target in TM_plain
    )
    print_tm(tm)
    most_often_appearing_target, target_n = TransitionMap.get_target_statistics(tm)
    node = BranchTable(copy(tm), most_often_appearing_target)
    print "    ---"
    for element in node.implement():
        print "    %s" % element,

    interval_begin = 0

adr0 = dial_db.new_address()
adr1 = dial_db.new_address()

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
