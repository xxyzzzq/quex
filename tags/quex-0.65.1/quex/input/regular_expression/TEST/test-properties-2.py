#! /usr/bin/env python
import sys
import os
import StringIO

sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.exception as exception
from   quex.input.regular_expression.engine import snap_character_set_expression

if "--hwut-info" in sys.argv:
    print "Unicode properties: Set Operations"
    sys.exit(0)
    
def test(TestString, NumbersF=False):
    print
    print "expression = \"" + TestString + "\""
    stream = StringIO.StringIO(TestString)
    try:
        result = snap_character_set_expression(stream, {})
        if NumbersF == False:
            print "result     = " + result.get_number_set().get_utf8_string() 
        else:
            print "result     = " + repr(result) 
    except exception.RegularExpressionException, x:
        print x.message

test("[: intersection(\\P{White_Space}, \\P{Block=Basic Latin}) :]")    
test("[: difference(\P{Script=Greek}, \G{Nd}) :]")
test("[: intersection(\P{Script=Gujarati}, \G{Nd}) :]")
test("[: intersection(\P{Script=Hebrew}, \G{Nd}) :]")
test("[: intersection(\P{Script=Arabic}, \G{Nd}) :]")
test("[: intersection(\G{Lu}, intersection(\\P{Hex_Digit}, \\P{Block=Basic Latin})) :]")    
