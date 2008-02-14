#! /usr/bin/env python
import test_NumberSet_base
import sys

if "--hwut-info" in sys.argv:
    print "NumberSet: Difference"
    sys.exit(0)

def the_difference(Comment, A, B):
    print "#\n#" + Comment
    print "#  A          = " + repr(A)
    print "#  B          = " + repr(B)
    print "#  difference(A,B) = " + repr(A.difference(B))
    print "#  difference(B,A) = " + repr(B.difference(A))

test_NumberSet_base.do("DIFFERENCE", the_difference)    

