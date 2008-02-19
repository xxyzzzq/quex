#! /usr/bin/env python
import test_NumberSet_base
import sys

if "--hwut-info" in sys.argv:
    print "NumberSet: Intersection"
    sys.exit(0)

def the_intersection(Comment, A, B):
    print "#\n#" + Comment
    print "#  A          = " + repr(A)
    print "#  B          = " + repr(B)
    print "#  intersection(A,B) = " + repr(A.intersection(B))
    print "#  intersection(B,A) = " + repr(B.intersection(A))

test_NumberSet_base.do("INTERSECTION", the_intersection)    
