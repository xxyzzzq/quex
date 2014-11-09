#! /usr/bin/env python
import sys
import os
from copy import deepcopy
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.misc.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Massive Mutual Consistency Check"
    print "CHOICES:   union, intersection, symmetric_difference, difference, is_superset;"
    print "SAME;"
    sys.exit(0)

class Tester:
    def __init__(self, Name1, Operation1, Name2, Operation2):
        self.__operation_1 = Operation1
        self.__operation_2 = Operation2
        self.name1 = Name1
        self.name2 = Name2

    def do(self, A, B):
        result1 = self.__operation_1(A, B)
        result2 = self.__operation_2(A, B)
        if type(result1) == bool:
            if result1 == result2: return True
        else:
            result1.assert_consistency()
            result2.assert_consistency()
            if result1.is_equal(result2): return True
                
        print "Error: %s vs. %s" % (self.name1, self.name2)
        print "Error: A = " + repr(A)
        print "Error: B = " + repr(B)
        print "%s: %s" % (self.name1, self.__operation_1(A, B))
        print "%s: %s" % (self.name2, self.__operation_2(A, B))
        return False

class NumberSetGenerator:
    def __init__(self):
        self.__cursor = [ 1 ] * 20
        self.N = 16

    def get(self):
        # Transform 'cursor' into a number set
        result = NumberSet()
        K   = len(self.__cursor)
        if K == 0: return None
        k   = 0
        end = 0
        while k < K - 1:
            begin = end   + self.__cursor[k]
            end   = begin + self.__cursor[k+1]
            if end > self.N: 
                self.__cursor.pop()
                K -= 1
                break
            if begin != end:
                result.quick_append_interval(Interval(begin, end))
            k += 2

        # Increment cursor
        k = 0
        while k < K:
            if k == 0:
                self.__cursor[k] += 2
                if self.__cursor[k] < 8: 
                    break
            else:
                self.__cursor[k] += 1
                if self.__cursor[k] < 3:
                    break
            self.__cursor[k] = 1
            k += 1

        return result

generator = NumberSetGenerator()

# Generate 100 NumberSets
number_set_list = []
for i in range(100):
    result = generator.get()
    number_set_list.append(generator.get())

def test(N1, Op1, N2, Op2):
    global number_set_list
    the_tester = Tester(N1, Op1, N2, Op2)

    # Permutate all existing intervals against each other
    count_n = 0
    for i, x in enumerate(number_set_list):
        for y in number_set_list[i + 1:]:
            if the_tester.do(x, y) == False: 
                print "## experiment number = ", count_n
                return
            if the_tester.do(y, x) == False: 
                print "## experiment number = ", count_n
                return
            count_n += 1

    print "Oll Korreckt: " + repr(count_n)

            
if "union" in sys.argv:
    def A_union_B(A, B):
        return A.union(B)

    def A_unite_with_B(A, B):
        result = deepcopy(A)
        result.unite_with(B)
        return result

    def not_BO_not_A_intersection_not_B_BC(A, B):
        x = A.inverse()
        y = B.inverse()
        result = x.intersection(y)
        return result.inverse()

    test("union", A_union_B,           "unite_with", A_unite_with_B)
    test("unite_with", A_unite_with_B, "not ...", not_BO_not_A_intersection_not_B_BC)

elif "intersection" in sys.argv:
    def A_intersection_B(A, B):
        return A.intersection(B)

    def A_intersect_with_B(A, B):
        result = deepcopy(A)
        result.intersect_with(B)
        return result

    def not_BO_not_A_union_not_B_BC(A, B):
        x = A.inverse()
        y = B.inverse()
        result = x.union(y)
        return result.inverse()

    test("intersection", A_intersection_B,     "intersect_with", A_intersect_with_B)
    test("intersect_with", A_intersect_with_B, "not ...",        not_BO_not_A_union_not_B_BC)

elif "difference" in sys.argv:
    def A_difference_B(A, B):
        return A.difference(B)

    def A_subtract_B(A, B):
        result = deepcopy(A)
        result.subtract(B)
        return result

    def A_intersection_not_B(A, B):
        result = deepcopy(A)
        result.intersect_with(B.inverse())
        return result

    test("difference", A_difference_B, "subtract",          A_subtract_B)
    test("subtract",  A_subtract_B,    "intersect not ...", A_intersection_not_B)

elif "symmetric_difference" in sys.argv:

    def symmetric_difference(A, B):
        return A.symmetric_difference(B)

    def A_union_B_minus_A_intersection_B(A, B):
        x = deepcopy(A)
        x.unite_with(B)
        y = deepcopy(A)
        y.intersect_with(B)
        x.subtract(y)
        return x

    test("symmetric_difference", symmetric_difference, "union minus intersection", A_union_B_minus_A_intersection_B)
    # No second test ... for uniformity:
    print "Oll Korreckt: 4950"

elif "is_superset" in sys.argv:
    # If A is a superset of B, then and only then 'B - A == 0' 
    def is_superset(A, B):
        return A.is_superset(B)

    def B_minus_A_is_empty(A, B):
        return B.difference(A).is_empty()

    test("is_superset", is_superset, "difference is empty", B_minus_A_is_empty)
    # No second test ... for uniformity:
    print "Oll Korreckt: 4950"
