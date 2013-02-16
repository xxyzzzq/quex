#! /usr/bin/env python
import sys
import os
import StringIO

sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.exception as exception
from   quex.input.regular_expression.engine import snap_character_set_expression

if "--hwut-info" in sys.argv:
    print "Combination: Alternative Expressions"
    sys.exit(0)
    
def test(TestString, NumbersF=False):
    print
    print "expression = \"" + TestString + "\""
    stream = StringIO.StringIO(TestString)
    try:
    # if True:
        result = snap_character_set_expression(stream, {})
        result = result.get_number_set()
        if NumbersF == False:
            if result.__class__.__name__ == "StateMachine":
                print "result     = " + result.get_string(NormalizeF=True) 
            else:
                print "result     = " + result.get_utf8_string() 
        else:
            if result.__class__.__name__ == "StateMachine":
                print "result     = " + result.get_string(NormalizeF=True) 
            else:
                print "result     = " + result.get_string()
    except exception.RegularExpressionException, x:
        print x.message


test("[: alnum :]",         NumbersF=True)    
test("[: [\\100-\\0] :]",   NumbersF=True)    
test("[: [\\x10-\\x40] :]", NumbersF=True)    
test("[: [\\X10-\\X40] :]", NumbersF=True)    
test("[: [\\U10-\\U40] :]", NumbersF=True)    
test("[: difference([0-9], [1,3,5,7,9]) :]")    
test("[: union([0-9], [a-z0-5]) :]")    
test("[: intersection([0-9], [a-z0-5]) :]")    
test("[: inverse([0-9]) :]")    

print 
print "And know something completely different ..."

test("[: difference([0-9], union([1-3], intersection([0-7], [5-9]))) :]")    
test("[: difference(alnum, digit) :]")    

def test2(TestString):
    stream = StringIO.StringIO(TestString)
    result = snap_character_set_expression(stream, {})

    print "expression = \"" + TestString + "\""
    print "result     = " + result.get_string(Option="hex", NormalizeF=True)

print 
print "Check the range cut ..."

test2("[^a]")
test2("[:inverse([a]):]")
