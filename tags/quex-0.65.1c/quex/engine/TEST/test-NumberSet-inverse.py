#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.interval_handling import Interval, NumberSet


if "--hwut-info" in sys.argv:
    print "NumberSet: Inverse"
    print "CHOICES: 1, 2, serious;"
    sys.exit(0)


def test(NSet):
    print "# write output in temporary file: 'tmp'"    
    print "# plot with gnuplot:"
    print "# > plot \"tmp\" w l"
    
    print NSet.gnuplot_string(1)
    result = NSet.inverse()
    result.assert_consistency()
    print result.gnuplot_string(0)

if "1" in sys.argv:
    test(NumberSet([Interval(10,20),   Interval(21,30),
                    Interval(50,70),   Interval(71,80),
                    Interval(80,81),   Interval(82,90),
                    Interval(90,100),  Interval(110,130),
                    Interval(150,170), Interval(171,190),
                    Interval(200,230), Interval(231,240),
                    Interval(250,260), Interval(261,280)]))
elif "2" in sys.argv:
    NSet = NumberSet(Interval(1, 0x10FFFE))
    print NSet.inverse()

elif "serious" in sys.argv:
    def test(X):
        print "#_______________________________________________"
        nset  = NumberSet([ Interval(x, y) for x, y in X])
        clone = nset.clone()
        print "#NumberSet:         %s" % nset
        result = nset.clone()
        result.invert()
        print "#NumberSet.inverse: %s" % result
        assert result.is_equal(nset.inverse())
        assert result.intersection(nset).is_empty()
        assert result.union(nset).is_all()

    test([(0,               100)])
    test([(0,               sys.maxint)])
    test([(-sys.maxint,     0)])
    test([(-sys.maxint,     sys.maxint)])

    test([(0,         100), (500, 600)])
    test([(0,         100), (500, sys.maxint)])
    test([(-sys.maxint, 0), (500, 600)])
    test([(-sys.maxint, 0), (500, sys.maxint)])

    test([(0,         100), (100, 200), (500, 600)])
    test([(0,         100), (100, 200), (500, sys.maxint)])
    test([(-sys.maxint, 0), (100, 200), (500, 600)])
    test([(-sys.maxint, 0), (100, 200), (500, sys.maxint)])

