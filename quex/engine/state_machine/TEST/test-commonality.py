#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine           as regex
import quex.engine.state_machine.commonality_checker as commonality_checker

if "--hwut-info" in sys.argv:
    print "Commonality Checker"
    # print "CHOICES: True, False, Pre-Post-Contexts-True, Pre-Post-Contexts-False;"
    sys.exit(0)
    
def test(A, B):
    def __core(Pattern0, Pattern1):
        print ("Pattern A = " + Pattern0).replace("\n", "\\n").replace("\t", "\\t")
        print ("Pattern B = " + Pattern1).replace("\n", "\\n").replace("\t", "\\t")
        sm0 = regex.do(Pattern0, {})
        sm1 = regex.do(Pattern1, {})
        print "claim     = ", commonality_checker.do(sm0, sm1)
    print "---------------------------"
    __core(A, B)
    print
    __core(B, A)

test("b", "ab")
test("a", "a")
test("a", "ab")
test("a", "a{5}")
test("albert", "a(de)?lbert")
test("(alb)|(er)", "albert")
test("(alb)+|(er)", "albert")
test("(alfons)|(adelheid)|(adolf)|(arthur)|(arnheim)|(augsburg)|(frieda)", "albert")
test("(alfons)|(adelheid)|(adolf)|(arthur)|(arnheim)|(augsburg)|(frieda)", "arthurius")
test("(a+lfons)|(a{2}delheid)|(a+dolf)|(a+r+t+h{1,3}ur)|(a+r+n+heim)|(a{5,}ugsburg)|(f+rieda)", "arthurius")
