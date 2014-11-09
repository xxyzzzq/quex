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
from   quex.output.core.state.transition_map.solution import get_Bisection   
from   quex.output.core.languages.core import db
from   quex.engine.misc.interval_handling        import Interval
from   quex.engine.analyzer.transition_map  import TransitionMap   
from   quex.blackboard                      import setup as Setup, \
                                                   Lng
from   collections import defaultdict

if "--hwut-info" in sys.argv:
    print "Code generation: Bisection;"
    sys.exit()

#if len(sys.argv) < 2: 
#    print "Not enough arguments"
#    exit()

Lang = "C"
N    = 0x3

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
        print "    %-7s -> %s" % (interval.get_string("hex"), target)

def test(TM_plain):
    global interval_begin

    print "#" + "-" * 79
    tm = TransitionMap.from_iterable(
        (interval, long(target)) for interval, target in TM_plain
    )
    print_tm(tm)
    most_often_appearing_target, target_n = TransitionMap.get_target_statistics(tm)
    node = get_Bisection(copy(tm))
    print "    ---"
    for element in node.implement():
        print "    %s" % element,

    interval_begin = 0

adr0 = dial_db.new_address()
adr1 = dial_db.new_address()
adr2 = dial_db.new_address()

test([
    (interval(N), adr0),
    (interval(N), adr1),
])
test([
    (interval(N), adr0),
    (interval(N), adr1),
    (interval(N), adr2),
])
test([
    (interval(N), adr0),
    (interval(N), adr1),
    (interval(N), adr2),
    (interval(N), adr0),
])
test([
    (interval(N), adr0),
    (interval(N), adr1),
    (interval(N), adr2),
    (interval(N), adr0),
    (interval(N), adr1),
])
