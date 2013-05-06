#! /usr/bin/env python
import sys
import os
import StringIO

sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.exception as exception

sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as engine

if "--hwut-info" in sys.argv:
    print "Anti-Patterns"
    sys.exit(0)
    
def test(TestString):
    print
    print "expression = \"" + TestString + "\""
    stream = StringIO.StringIO(TestString)
    try:
        result = engine.do(stream, {})
        print "result     = " + result.get_string(Option="hex", NormalizeF=True) 
    except exception.RegularExpressionException, x:
        print x.message

test("\\A{for}")    
test("\\A{[ab][cd][de]}")    
test("\\A{x+y+}")    
