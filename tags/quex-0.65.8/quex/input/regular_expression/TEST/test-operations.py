#! /usr/bin/env python
# vim:fileencoding=utf8 
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
from   quex.input.regular_expression.exception import RegularExpressionException
from   quex.blackboard import setup as Setup
Setup.set_all_character_set_UNIT_TEST(-sys.maxint, sys.maxint)
Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Operations;"
    print "CHOICES: special, 0, 1, 2, 3;"
    sys.exit(0)
    
def test(TestString):
    print "-------------------------------------------------------------------"
    print "expression    = \"" + TestString + "\""
    try: 
        sm = core.do(TestString, {})
        print "state machine\n", sm 

    except RegularExpressionException, x:
        print x._message
    except:
        pass

if "special" in sys.argv:
    test("\\Any")
    test("\\Any+")
    test("x\\Any*")
    test("\\Any*")
    test("x\\None")
    test("\\None")
    sys.exit()
elif   "0" in sys.argv:
    args = ""
elif "1" in sys.argv:
    args = "[a-z]+"
elif "2" in sys.argv:
    args = "[a-k]+ [g-p]+"
elif "3" in sys.argv:
    args = "[a-k]+ [g-p]+ [j-z]+"

test("\\A{%s}" % args)
test("\\C{%s}" % args)
test("\\Diff{%s}" % args)
test("\\Intersection{%s}" % args)
test("\\NotBegin{%s}" % args)
test("\\NotEnd{%s}" % args)
test("\\Not{%s}" % args)
test("\\R{%s}" % args)
test("\\SymDiff{%s}" % args)
#test("\\Tie{%s}" % args.replace("+", ""))
test("\\Union{%s}" % args)
#test("\\Untie{%s}" % args)

