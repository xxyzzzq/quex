#! /usr/bin/env python
import sys
import os
from StringIO import StringIO
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
from quex.exception  import *
from quex.input.regular_expression.auxiliary import PatternShorthand
from quex.blackboard import setup as Setup

Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Replacement: Regular Expression State Machines"
    sys.exit(0)

def test(TestString, PatternDict):
    try:
        print "expression    = " + TestString 
        print "state machine\n", core.do(TestString, PatternDict)
    except RegularExpressionException, x:
        print "Expression Expansion:\n" + repr(x)

pattern_dict = { "DIGIT":      '[0-9]', 
                 "NAME":       '[A-Z][a-z]+', 
                 "NUMBER":     '{DIGIT}("."{DIGIT}*)?',
                 "IDENTIFIER": '[_a-z][_a-z0-9]*',
                 "SPACE":      '[ \t\n]'
}

try:
    adapted_dict = {}
    for key, regular_expression in pattern_dict.items():
        string_stream = StringIO(regular_expression)
        state_machine = core.do(string_stream, adapted_dict).sm
        # It is ESSENTIAL that the state machines of defined patterns do not 
        # have origins! Actually, there are not more than patterns waiting
        # to be applied in regular expressions. The regular expressions 
        # can later be origins.

        adapted_dict[key] = PatternShorthand(key, state_machine)
except RegularExpressionException, x:
    print "Dictionary Creation:\n" + repr(x)


test('{DIGIT}("."{DIGIT}*)?', adapted_dict)
test('{NAME}("."{DIGIT}*)?', adapted_dict)
test('FOR{SPACE}+{NAME}{SPACE}={NUMBER}', adapted_dict)

