#! /usr/bin/env python
import sys
import os
from StringIO import StringIO
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core

from quex.input.regular_expression.engine import snap_set_expression
from quex.input.regular_expression.exception        import *
from quex.input.regular_expression.auxiliary import PatternShorthand
from quex.blackboard       import setup as Setup
Setup.buffer_limit_code = 0
Setup.path_limit_code   = 0

if "--hwut-info" in sys.argv:
    print "Replacement: Character Sets"
    sys.exit(0)

def test(TestString, PatternDict):
    print "-------------------------------------------"
    TestString = "[:" + TestString + ":]"
    stream = StringIO(TestString)
    print "expression    = " + TestString 
    try:
        print "character set = " + snap_set_expression(stream, PatternDict).get_string(Option="hex")
    except RegularExpressionException, x:
        print "Expression Expansion:\n" + repr(x)

pattern_dict = { "DIGIT":      '[0-9]', 
                 "LETTER":     '[A-Z]', 
                 "GREEK":      '[: \\P{Script=Greek} :]', 
                 "SPACE":      '[ \t\n]'
}

try:
    adapted_dict = {}
    for key, regular_expression in pattern_dict.items():
        string_stream = StringIO(regular_expression)

        state_machine = core.do(string_stream, adapted_dict).sm

        adapted_dict[key] = PatternShorthand(key, state_machine)

except RegularExpressionException, x:
    print "Dictionary Creation:\n" + repr(x)


test('intersection([\\X0-\\XFFFF], {DIGIT})', adapted_dict)
test('{LETTER}', adapted_dict)
test('union({DIGIT}, {LETTER}, {GREEK}, {SPACE})', adapted_dict)

