#! /usr/bin/env python
# -*- coding: utf8 -*-
# 
# 'can_be_moved_to_tail(CL, i, ExceptionSet)' checks whether the command 
# at position 'i' can be moved to the tail, given that all k in ExceptionSet
# do not have to be considered. The moving is obstructed, if the command
# is not switchable with another (due to interferring register access).
#
# A command that reads a register A can obviously not be moved to the tail, 
# if there is another command writes into register A. Let R be the reading
# command and W the writing command.
#
#                        ..
#            size = 0    ||
#                        ''
#                        .-.  
#            size = 1    |R|  
#                        '-'  
#                        .-.-. .-.-.   
#            size = 2    | |R| |W|R|   
#                        '-'-' '-'-'   
#                        .-.-. .-.-.   
#                        |R| | |R|W|   
#                        '-'-' '-'-'   
#                        .-.-.-.  .-.-.-.  .-.-.-.  .-.-.-.  
#            size = 3    | | |R|  | |W|R|  |W| |R|  |W|W|R|
#                        '-'-'-'  '-'-'-'  '-'-'-'  '-'-'-'
#                        .-.-.-.  .-.-.-.  .-.-.-.  .-.-.-. 
#                        | |R| |  | |R|W|  |W|R| |  |W|R|W| 
#                        '-'-'-'  '-'-'-'  '-'-'-'  '-'-'-' 
#                        .-.-.-.  .-.-.-.  .-.-.-.  .-.-.-.
#                        |R| | |  |R| |W|  |R|W|W|  |R|W|W|
#                        '-'-'-'  '-'-'-'  '-'-'-'  '-'-'-'
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

import os 
import sys 
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.blackboard                            import E_Cmd
from   quex.engine.analyzer.commands.core         import *
from   quex.engine.analyzer.commands.shared_tail  import r_can_be_moved_to_tail
from   quex.engine.analyzer.commands.TEST.helper  import *
from   quex.engine.analyzer.door_id_address_label import DoorID

from   collections import defaultdict
from   itertools   import izip, permutations
from   copy        import deepcopy

if "--hwut-info" in sys.argv:
    print "Command.shared_tail: can_be_moved_to_tail;"
    print "CHOICES: no-exceptions, with-exceptions;"
    sys.exit()

def test(Setting, ExceptionSet=set()):
    cl = [ rw_get(flag) for flag in Setting ]

    txt  = "   Setting: [%s]" % "".join(Setting)
    if len(ExceptionSet) != 0: 
        txt += " w/o %s " % list(ExceptionSet)

    if len(cl): i = Setting.index("R")
    else:       i = 0
    L = len(cl)
    if L == 0: 
         print "len(cl) == 0 is not allowed."
         return

    cl_r           = list(reversed(cl))
    i_r            = L - 1 - i
    ExceptionSet_r = set(L - 1 - i for i in ExceptionSet)
    txt += " %s" % r_can_be_moved_to_tail(cl_r, i_r, ExceptionSet_r)

    print txt

if "no-exceptions" in sys.argv:
    print "Size 0 _________________________________________________________________"
    print
    test([])

    print
    print "Size 1 _________________________________________________________________"
    print
    test(["R"])
    print
    print "Size 2 _________________________________________________________________"
    print
    for setting in rw_generator(2):
        test(setting)

    print
    print "Size 3 _________________________________________________________________"
    print
    for setting in rw_generator(3):
        test(setting)

    print
    print "Size 4 _________________________________________________________________"
    print
    for setting in rw_generator(3):
        test(setting)
    print

if "with-exceptions" in sys.argv:
    for i in xrange(3):
        test(["R", " ", " "], set([i]))
    for i in xrange(3):
        test(["R", " ", "W"], set([i]))
    for i in xrange(3):
        test(["R", "W", " "], set([i]))
    for i in xrange(3):
        test(["R", "W", "W"], set([i]))
    for i in xrange(3):
        test(["R", "W", "W"], set([1, i]))



