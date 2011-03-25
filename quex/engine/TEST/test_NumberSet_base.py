#! /usr/bin/env python
import sys
import os
from copy import deepcopy

sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.core_engine.interval_handling import Interval, NumberSet

A6 = None
def do(Title, func, PlotF=True):
    global A6

    A0 = NumberSet([Interval(10,20), Interval(21,30)])
    B0 = NumberSet([Interval(0,40)])
    func("(a) one interval overlaps all of the others",
         A0,B0)

    A1 = NumberSet([Interval(50,70), Interval(71,80)])
    B1 = NumberSet([Interval(40,60)])
    func("(b) one interval overlaps the lower of the others",
         A1,B1)

    A2 = NumberSet([Interval(90,100), Interval(11,130)])
    B2 = NumberSet([Interval(120,140)])
    func("(c) one interval overlaps the upper of the others",
         A2,B2)

    A3 = NumberSet([Interval(150,170), Interval(171,190)])
    B3 = NumberSet([Interval(160,180)])
    func("(d) one interval overlaps the middle of the others",
         A3,B3)

    A4 = NumberSet([Interval(200,230), Interval(231,240)])
    B4 = NumberSet([Interval(220,250)])
    func("(e) one interval overlaps the 1st a little, the second totally",
         A4,B4)

    A5 = NumberSet([Interval(250,260), Interval(261,280)])
    B5 = NumberSet([Interval(240,270)])
    func("(d) one interval overlaps the 2nd a little, the first totally",
         A5,B5)

    A6 = NumberSet()
    A6 = A6.union(A0).union(A1).union(A2).union(A3).union(A4).union(A5)
    B6 = NumberSet()
    B6 = B6.union(B0).union(B1).union(B2).union(B3).union(B4).union(B5)
    func("(e) all together",
         A6,B6)

    if not PlotF: return
    print "# write output in temporary file: 'tmp'"    
    print "# plot with gnuplot:"
    print "# > plot \"tmp\" w l"

    print A6.gnuplot_string(4)
    print B6.gnuplot_string(3)
    if Title == "UNION":
        print A6.union(B6).gnuplot_string(1)
        print B6.union(A6).gnuplot_string(0)
    elif Title == "INTERSECTION":
        print A6.intersection(B6).gnuplot_string(1)
        print B6.intersection(A6).gnuplot_string(0)
    elif Title == "DIFFERENCE":
        print A6.difference(B6).gnuplot_string(1)
        print B6.difference(A6).gnuplot_string(0)
    elif Title == "CUT_INTERVAL":
        X = deepcopy(A6)
        for interval in B6.get_intervals():
            X.cut_interval(interval)
        print X.gnuplot_string(1)
        Y = deepcopy(B6)
        for interval in A6.get_intervals():
            Y.cut_interval(interval)
        print Y.gnuplot_string(0)
    elif Title == "CLEAN":
        X = deepcopy(A6)
        for interval in B6.get_intervals():
            X.quick_append_interval(interval)
        X.clean()
        print X.gnuplot_string(1)

        X = deepcopy(B6)
        for interval in A6.get_intervals():
            X.quick_append_interval(interval)
        X.clean()
        print X.gnuplot_string(0)

        




    
    
