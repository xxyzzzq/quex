#! /usr/bin/env python
import sys
import test_NumberSet_base

if "--hwut-info" in sys.argv:
    print "NumberSet: Union"
    sys.exit(0)

def the_union(Comment, A, B):
    print "#\n#" + Comment
    print "#  A          = " + repr(A)
    print "#  B          = " + repr(B)
    print "#  union(A,B) = " + repr(A.union(B))
    print "#  union(B,A) = " + repr(B.union(A))


test_NumberSet_base.do("UNION", the_union)
