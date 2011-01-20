#! /usr/bin/env python
import sys
import os
import StringIO

sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.exception as exception
import quex.core_engine.regular_expression.character_set_expression as character_set_expression

if "--hwut-info" in sys.argv:
    print "Combination: Alternative Expressions"
    sys.exit(0)
    
def test(TestString, NumbersF=False):
    print
    print "expression = \"" + TestString + "\""
    stream = StringIO.StringIO(TestString)
    try:
        result = character_set_expression.snap_set_expression(stream, {})
        if NumbersF == False:
            print "result     = " + result.get_utf8_string() 
        else:
            print "result     = " + repr(result) 
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
    result = character_set_expression.do(stream, {})

    print "expression = \"" + TestString + "\""
    print "result     = " + result.get_string(Option="hex")

print 
print "Check the range cut ..."

test2("[^a]")
test2("[:inverse([a]):]")
