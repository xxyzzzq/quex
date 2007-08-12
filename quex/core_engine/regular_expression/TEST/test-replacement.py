#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core

if "--hwut-info" in sys.argv:
    print "pattern identifier replacement"
    sys.exit(0)
    
def test(TestString, PatterDict):
    print "expression    = \"" + TestString + "\""
    print "state machine\n", core.do(TestString, PatterDict)

pattern_dict = { "DIGIT":      '[0-9]', 
                 "NAME":       '[A-Z][a-z]+', 
		 "NUMBER":     '{DIGIT}("."{DIGIT}*)?',
		 "IDENTIFIER": '[_a-z][_a-z0-9]*',
                 "SPACE":      '[ \t\n]'
}

test('{DIGIT}("."{DIGIT}*)?', pattern_dict)
test('{NAME}("."{DIGIT}*)?', pattern_dict)
test('FOR{SPACE}+{NAME}{SPACE}={NUMBER}', pattern_dict)

