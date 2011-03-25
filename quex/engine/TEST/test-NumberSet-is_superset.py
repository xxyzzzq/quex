#! /usr/bin/env python
import test_NumberSet_base
import sys
import os
from copy import deepcopy
sys.path.append(os.environ["QUEX_PATH"])
from quex.core_engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Super Set;"
    print "CHOICES:   Normal, Examples;"
    sys.exit(0)


def prepare(A_list, B_list):
    A = NumberSet()
    B = NumberSet()
    for begin, end in A_list:
        A.add_interval(Interval(begin, end))
    for begin, end in B_list:
        B.add_interval(Interval(begin, end))
    return A, B

def test(Comment, A_list, B_list):
    if type(A_list) != list: A = A_list; B = B_list;
    else:                    A, B = prepare(A_list, B_list)

    print "#\n#" + Comment
    print "#  A = " + repr(A)
    print "#  B = " + repr(B)
    print "#  A.is_superset(B) = " + repr(A.is_superset(B))
    print "#  B.is_superset(A) = " + repr(B.is_superset(A))

if "Normal" in sys.argv:
    # Check some well chosen number sets
    test_NumberSet_base.do("is_superset", test, PlotF=False)    
elif "Examples" in sys.argv:
    test("is_superset", 
         [[0, 1], [2, 3]],
         [[0, 1]])
    test("is_superset", 
         [[0, 1], [2, 3]],
         [[2, 3]])
    test("is_superset", 
         [[0, 1], [2, 3], [4, 5]],
         [[2, 3]])
    test("is_superset", 
         [[0, 1], [2, 3], [4, 5]],
         [[1, 3]])
    test("is_superset", 
         [[0, 1], [2, 3], [4, 5]],
         [[2, 4]])
    test("is_superset", 
         [[0, 1], [2, 3], [4, 5]],
         [[1, 4]])
    test("is_superset", 
         [[1, 2], [3, 4], [5, 6]],
         [[1, 6]])
    test("is_superset", 
         [[1, 2], [3, 4], [5, 6]],
         [[0, 6]])
    test("is_superset", 
         [[1, 2], [3, 4], [5, 6]],
         [[1, 7]])
