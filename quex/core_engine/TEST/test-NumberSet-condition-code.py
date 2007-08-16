#! /usr/bin/env python
# PURPOSE: Test the code generation for number sets. Two outputs are generated:
#
#           (1) stdout: containing value pairs (x,y) where y is 1.8 if x lies
#               inside the number set and 1.0 if x lies outside the number set.
#           (2) 'tmp2': containing the information about the number set under
#               consideration.
#
# The result is best viewed with 'gnuplot'. Call the program redirect the stdout
# to file 'tmp2' and type in gnuplot:
#
#         > plot [][0.8:2] "tmp2" w l, "tmp" w p
################################################################################
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.core_engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Condition Code Generation"
    sys.exit(0)


A0 = NumberSet([Interval(10,20),    Interval(21,30),
                Interval(50,70),    Interval(71,80),
                Interval(90,100),   Interval(110,130),
                Interval(150,151),  Interval(151,190),
                Interval(190,195),  Interval(195,196), 
                Interval(197, 198), Interval(198, 198),
                Interval(200,230),  Interval(231,240),
                Interval(250,260),  Interval(261,280)])


function = A0.condition_code("Python", "example_func")
exec(function)

fh = open("tmp2", "w")
fh.write(A0.gnuplot_string(1) + "\n")

for number in range(300):
    if example_func(number):  sys.stdout.write("%i 1.0\n\n" % number)
    else:                     sys.stdout.write("%i 1.8\n\n" % number)

