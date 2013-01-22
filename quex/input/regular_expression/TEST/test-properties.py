#! /usr/bin/env python
import sys
import os
import StringIO

sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.exception as exception

sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.input.regular_expression.engine import snap_character_set_expression

if "--hwut-info" in sys.argv:
    print "Unicode properties: Simple"
    sys.exit(0)
    
def test(TestString, NumbersF=False, HexF=False):
    print
    print "expression = \"" + TestString + "\""
    stream = StringIO.StringIO(TestString)
    try:
        result = snap_character_set_expression(stream, {})
        if NumbersF == False:
            print "result     = " + result.get_utf8_string() 
        elif HexF:
            print "result     = " + result.get_string(Option="hex") 
        else:
            print "result     = " + repr(result) 
    except exception.RegularExpressionException, x:
        print x.message

test("\\P{White_Space}", NumbersF=True)    
test("\\P{Hex_Digit}")    
test("\\P{Name=KANGXI RADICAL RICE}", NumbersF=True)    
test("\\P{Block=Arabic}", NumbersF=True)    
test("\\P{Script=Arabic}", NumbersF=True)    
test("\\N{KANGXI RADICAL RICE}", NumbersF=True)    
test("\\G{KANGXI RADICAL RICE}", NumbersF=True)    
test("\\G{Nd}")    
test("\\E{iso8859_6}", NumbersF=True, HexF=True)    
test("\\E{cp737}", NumbersF=True, HexF=True)    
