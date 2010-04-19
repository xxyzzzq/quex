#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.templates as templates 


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Target Idx Combination Metric"
    print "CHOICES: 1, 2, 2b, 3, 4;"
    sys.exit(0)

def print_tm(TM):
    cursor = 0
    txt = [" "] * 40
    for info in TM[1:]:
        x = max(0, min(40, info[0].begin))
        txt[x] = "|"

    txt[0]  = "|"
    txt[39] = "|"
    print "".join(txt),

    txt = ""
    for info in TM:
        if type(info[1]) != list: txt += "%i, " % info[1]
        else:                     txt += "%s, " % repr(info[1])
    txt = txt[:-2] + ";"
    print "   " + txt

def print_metric(M):
    print "BorderN     = %i" % M[0]
    print "TargetCombN = %s" % repr(M[1])[1:-1].replace("[", "(").replace("]", ")")

def test(TMa, TMb):
    print
    print "(Straight)---------------------------------------"
    print
    print_tm(TMa)
    print_tm(TMb)
    print
    print_metric(templates.get_metric(TMa, TMb))
    print
    print "(Vice Versa)-------------------------------------"
    print
    print_tm(TMb)
    print_tm(TMa)
    print
    print_metric(templates.get_metric(TMb, TMa))
    print

tm0 = [ 
        (Interval(-sys.maxint, 10), [10L, 11L]),
        (Interval(10, sys.maxint),  [20L, 21L]),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 30), [10L, 11L]),
            (Interval(30, sys.maxint),  [20L, 21L]),
          ]
    test(tm0, tm1)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [20L, 21L]),
            (Interval(10, sys.maxint),  [10L, 11L])
          ]
    test(tm0, tm1)

elif "2b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [10L, 11L]),
            (Interval(10, sys.maxint),  [20L, 21L]),
          ]
    test(tm0, tm1)

elif "3" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 5),  [20L, 21L]),
            (Interval(5, 15),           [30L, 31L]),
            (Interval(20, 25),          [40L, 41L]),
            (Interval(25, 30),          [50L, 51L]),
            (Interval(35, sys.maxint),  [10L, 20L]),
          ]
    test(tm0, tm1)

elif "4" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, sys.maxint), [20L, 21L]),
          ]
    tm1 = [ 
            (Interval(-sys.maxint, 20), [20L, 21L]), 
            (Interval(20, sys.maxint),  [10L, 11L]), 
          ]
    test(tm0, tm1)

