#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.templates as templates 


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Single Target Idx Metric"
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
        txt += "%i, " % info[1]
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
        (Interval(-sys.maxint, 10), 1L),
        (Interval(10, sys.maxint),  2L),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 30), 1L),
            (Interval(30, sys.maxint),  2L),
          ]
    test(tm0, tm1)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), 2L),
            (Interval(10, sys.maxint),  1L),
          ]
    test(tm0, tm1)

elif "2b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), 1L),
            (Interval(10, sys.maxint),  2L),
          ]
    test(tm0, tm1)

elif "3" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 5),  2L),
            (Interval(5, 15),           3L),
            (Interval(20, 25),          4L),
            (Interval(25, 30),          5L),
            (Interval(35, sys.maxint),  1L),
          ]
    test(tm0, tm1)

elif "4" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, sys.maxint), 2L),
          ]
    tm1 = [ 
            (Interval(-sys.maxint, 20), 2L),
            (Interval(20, sys.maxint),  1L),
          ]
    test(tm0, tm1)

