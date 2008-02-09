#! /usr/bin/env python
import sys
sys.path.append("../")
import map_utf8_set 

def test(TestString):
        print "expression    = ", TestString
        print "state machine\n", map_utf8_set.do(TestString)

test("a-z")
test("ABCDE0-9")
test("ABCD\\aE0-9")
test("A-Z\\n^CD")
