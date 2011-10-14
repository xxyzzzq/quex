#! /usr/bin/env python
import sys
sys.path.append("../")
from quex.engine.interval_handling import Interval


def the_union(Comment, A, B):
    print "\n" + Comment
    print "  A          = " + repr(A)
    print "  B          = " + repr(B)
    print "  union(A,B) = " + repr(A.union(B))
    print "  union(B,A) = " + repr(B.union(A))

def the_intersection(Comment, A, B):
    print "\n" + Comment
    print "  A          = " + repr(A)
    print "  B          = " + repr(B)
    print "  intersection(A,B) = " + repr(A.intersection(B))
    print "  intersection(B,A) = " + repr(B.intersection(A))

def the_difference(Comment, A, B):
    print "\n" + Comment
    print "  A          = " + repr(A)
    print "  B          = " + repr(B)
    print "  difference(A,B) = " + repr(A.difference(B))
    print "  difference(B,A) = " + repr(B.difference(A))

def the_inverse(Comment, A):
    print "\n" + Comment
    print "  A          = " + repr(A)
    print "  inverse(A) = " + repr(A.inverse())


def test(Title, test):

    print Title
    print "------------------------------------------------------------------------------"
    test("(a) disjunct intervals",
         Interval(40,   500),
         Interval(1000, 10000))
    test("(b) disjunct intervals adjacent",
         Interval(40,   500),
         Interval(500, 10000))
    test("(c) intersecting intervals",
         Interval(40,   5000),
         Interval(1000, 10000))
    test("(d) intersecting intervals adjacent",
         Interval(40,   5000),
         Interval(4999, 10000))
    test("(e) same intervals",
         Interval(40, 5000),
         Interval(40, 5000))
    test("(f) one empty",
         Interval(),
         Interval(0, 5000))
    test("(g) both empty",
         Interval(),
         Interval())
    test("(h) overlap",
         Interval(0,50),
         Interval(10, 20))
    test("(i) overlap adjacent top",
         Interval(0,20),
         Interval(10, 20))
    test("(j) overlap adjacent bottom",
         Interval(0,50),
         Interval(0, 20))


def test_inverse():
    print "INVERSE"
    print "--------------------------------------------------------------------------------"
    
    the_inverse("(a) normal",
                Interval(5000,6000))
    the_inverse("(b) lower border = - maxint",
                Interval(-sys.maxint,6000))
    the_inverse("(c) upper border = maxint",
                Interval(5000,sys.maxint))
    the_inverse("(c) upper/lower border = +/- maxint",
                Interval(-sys.maxint,sys.maxint))
    


# test("UNION", the_union)
# test("INTERSECTION", the_intersection)
# test("DIFFERENCE", the_difference)
test_inverse()
