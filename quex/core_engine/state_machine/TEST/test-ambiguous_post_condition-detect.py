#! /usr/bin/env python
import sys
import os
from StringIO import StringIO
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.exception import RegularExpressionException
from quex.core_engine.state_machine.core import *
import quex.core_engine.regular_expression.core              as regex
import quex.core_engine.state_machine.ambiguous_post_context as apc

if "--hwut-info" in sys.argv:
    print "Pseudo Ambigous Post Condition: Detection"
    sys.exit(0)

def __test(RE_Core, RE_PostCondition):
    string_stream_Core          = StringIO(RE_Core)
    string_stream_PostCondition = StringIO(RE_PostCondition)

    try:
        core_sm           = regex.do(string_stream_Core, {})
    except RegularExpressionException, x:
        print "Core Pattern:\n" + repr(x)
        return

    try:
        post_context_sm = regex.do(string_stream_PostCondition, {})
    except RegularExpressionException, x:
        print "Post Condition Pattern:\n" + repr(x)
        return

    print "---------------------------------------------------------"
    print "core pattern            =", RE_Core
    print "post condition pattern  =", RE_PostCondition
    print "ambiguity (fw), (bw)    =", apc.detect_forward(core_sm, post_context_sm), \
                                   ", ", apc.detect_backward(core_sm, post_context_sm)

def test(RE_Core, RE_PostCondition):
    __test(RE_Core, RE_PostCondition)
    __test(RE_PostCondition, RE_Core)

test("ab", "ab")
test("a(b)*", "ab")
test("(a)+", "ab")
test('"xyz"+', '"xyz"')
test('"xyz"+', '"xyz"+')
test('"xyz"+', '[a-z]{4}')
test('"xyz"+', '("abc"|"xyz")')
test('"xyz"+', '("abc")|(("x"|"X")[a-z]{1}("z"|"Z"))')
test('("abc"+|"xyz")+', '("abc")|(("x"|"X")[a-z]{1}("z"|"Z"))')
test('("xyz")+hello', '"xyz"hello')
test('(("xyz")+hello)+', '"xyz"hello')
test("(.)+a", "(.)+")


