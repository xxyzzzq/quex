#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.core_engine.interval_handling import Interval, NumberSet


if "--hwut-info" in sys.argv:
    print "NumberSet: Inverse"
    sys.exit(0)


def test(NSet):
    print "# write output in temporary file: 'tmp'"    
    print "# plot with gnuplot:"
    print "# > plot \"tmp\" w l"
    
    print NSet.gnuplot_string(1)
    print NSet.inverse().gnuplot_string(0)



test(NumberSet([Interval(10,20),   Interval(21,30),
                Interval(50,70),   Interval(71,80),
                Interval(80,81),   Interval(82,90),
                Interval(90,100),  Interval(110,130),
                Interval(150,170), Interval(171,190),
                Interval(200,230), Interval(231,240),
                Interval(250,260), Interval(261,280)]))


