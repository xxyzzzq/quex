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
from   quex.output.core.state.transition_map.branch_table import BranchTable   
from   quex.output.core.languages.core import db
from   quex.engine.misc.interval_handling        import Interval
from   quex.engine.analyzer.transition_map  import TransitionMap   
from   quex.blackboard                      import setup as Setup, \
                                                   Lng
from   collections import defaultdict

if "--hwut-info" in sys.argv:
    print "Code generation: Branch Table (switch-case) II;"
    print "CHOICES: C-7, C-8, C-9, C-15, C-16, C-17, C-31, C-32, C-33;"
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
    prev = "\n"
    print "    ---"
    for element in node.implement():
        if prev and prev[-1] == "\n": print "    %s" % element,
        else:                         print element,
        prev = element

    interval_begin = 0

adr0 = dial_db.new_address()
adr1 = dial_db.new_address()

test([
    (interval(N), adr0),
    (interval(100), adr1),
])
test([
    (interval(1), adr1),
    (interval(N), adr0),
    (interval(100), adr1),
])
test([
    (interval(2), adr1),
    (interval(N), adr0),
    (interval(100), adr1),
])
test([
    (interval(7), adr1),
    (interval(N), adr0),
    (interval(100), adr1),
])
test([
    (interval(8), adr1),
    (interval(N), adr0),
    (interval(100), adr1),
])
test([
    (interval(9), adr1),
    (interval(N), adr0),
    (interval(100), adr1),
])
