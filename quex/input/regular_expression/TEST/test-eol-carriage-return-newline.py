#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
from quex.blackboard import setup as Setup
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

    Setup.dos_carriage_return_newline_f = True

    pattern = core.do(TestString, {})
    pattern.mount_post_context_sm()
    pattern.mount_pre_context_sm()
    if pattern is None: 
        print "pattern syntax error"
    else:
        print "pattern\n", pattern 
        print "begin of line = ", pattern.pre_context_trivial_begin_of_line_f

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
