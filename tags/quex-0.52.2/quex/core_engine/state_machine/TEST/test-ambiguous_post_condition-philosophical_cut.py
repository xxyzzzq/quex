#! /usr/bin/env python
import sys
import os
from StringIO import StringIO
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.exception                                          import RegularExpressionException
from quex.core_engine.state_machine.core                     import *
import quex.core_engine.regular_expression.core              as regex
import quex.core_engine.state_machine.ambiguous_post_context as apc
from   quex.input.setup import setup
setup.buffer_limit_code = -1
setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Pseudo Ambigous Post Condition: The Philosophical Cut"
    sys.exit(0)

def __test(RE_Core, RE_PostCondition):
    print "---------------------------------------------------------"
    print "core pattern            =", RE_Core
    print "post condition pattern  =", RE_PostCondition
    string_stream_Core          = StringIO(RE_Core)
    string_stream_PostCondition = StringIO(RE_PostCondition)

    try:
        core_sm           = regex.do(string_stream_Core, {})
    except RegularExpressionException, x:
        print "Core Pattern:\n" + repr(x)
        return

    try:
        post_context_sm = regex.do(string_stream_PostCondition, {})
        print "post condition sm = ", post_context_sm
    except RegularExpressionException, x:
        print "Post Condition Pattern:\n" + repr(x)
        return

    result_post_sm = apc.philosophical_cut(core_sm, post_context_sm)
    print "philosophical cut (in post condition) = "
    print result_post_sm

def test(RE_Core, RE_PostCondition):
    __test(RE_Core, RE_PostCondition)

test('"xy"+', '"xy"+')
test('(xy)+', '(xy)*z')
# test('(xy)*', '(xy)+z') --> surreal core pattern
# test('w(xy)+', '(xy)*') --> surreal post condition
test('w(xy)*', '(xy)+')
test('w(xy)+', '(xy)*z')
test('w(xy)*', '(xy)+z')
test('"xy"+', '("ab"|"xy")+')
test('"xy"+', '("abc")|((x[a-z])+z)')
test('"xy"+', '("abc")|(([a-z]y)+z)')
test('(hey)+', '(he[y]?)+')
test('(.)+a', '(.)+')



