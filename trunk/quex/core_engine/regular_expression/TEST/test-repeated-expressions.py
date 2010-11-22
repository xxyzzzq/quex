#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core
from quex.input.setup import setup as Setup
Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Combination: Simple repeated expressions"
    sys.exit(0)

def test(TestString):
    print "___________________________________________________________________________"
    print "expression    = \"" + TestString.replace("\n", "\\n") + "\""
    print "state machine\n", core.do(TestString, {}, AllowNothingIsNecessaryF=True)


test("[a-z]")
test('[a-z]+')
test('[a-z]*')
test('[a-z]?')
test('[a-z]{2,5}')
test('[a-z]{3,}')
test('[a-z]{4}')
test('"You"{3}')
test('"You"*')
test('"You"+')
test('"You"?')
test('a+(b|c)*t')
test('(\\n\\n)+')
test('(ab)+')
test('([ab]|"bc")*c')
