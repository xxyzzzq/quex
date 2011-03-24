#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core
from quex.input.setup import setup as Setup
Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Conditional Analysis: End of Line '$' (with DOS/Windows '\\r\\n')"
    sys.exit(0)

def test(TestString):
    test_core("^" + TestString + "$")

def test_core(TestString):
    print "___________________________________________________________________________"
    print "expression    = \"" + TestString + "\""
    sm = core.do(TestString, {}, DOS_CarriageReturnNewlineF=True)
    if sm == None: 
        print "pattern syntax error"
    else:
        print "state machine\n", sm 
        print "begin of line = ", sm.core().pre_context_begin_of_line_f()

test('[a-z]+')
# test('[a-z]*')
# test('[a-z]?')
# test("[a-z]?/[a-z]/")
test("[a-b]/[c-z]")
#test('[a-z]{2,5}')
#test('[a-z]{3,}')
#test('[a-z]{4}')
#test('"You"{3}')
#test('"You"*')
#test('"You"+')
#test('"You"?')
#test('a+(b|c)*t')
