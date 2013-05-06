#! /usr/bin/env python
import sys
import StringIO
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core

if "--hwut-info" in sys.argv:
    print "Basics: Snap string until (low level function)"
    sys.exit(0)


count_n = 0

def test(the_string, ClosingDelimiter, OpenDelimiter=None):
    global count_n
    count_n += 1
    print "%02i  regular expression = '" % count_n + the_string + "'"
    print "    opening delimiter  = " + repr(OpenDelimiter)
    print "    closing delimiter  = " + repr(ClosingDelimiter)
    print "    --------------------------------------------------------"
    stream = StringIO.StringIO(the_string)
    result = core.__snap_until(stream, ClosingDelimiter, OpenDelimiter)
    remainder = stream.read()
    print "    remaining string   = '%s'" % result
    print "    cut string         = '%s'" % remainder
    print "===========================================================" 


print "===========================================================" 
test('read until"and then return', "\"")    
test('read until\\"and"then return', "\"")    
test('read [ anything [ nicely ] bracketed until ] here ] and return', "]", "[")    
test('[ anything \\[ nicely \\\\] bracketed \\] until here ] and ] return', "]", "[")    
test('] and ] return', "]", "[")    
test('\\\\\\] until here ] and ] return', "]", "[")    
test('\\] until here \\\\]', "]", "[")    
