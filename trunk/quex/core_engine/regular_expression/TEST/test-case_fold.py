#! /usr/bin/env python
# vim:fileencoding=utf8 
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core

if "--hwut-info" in sys.argv:
    print "Case Folding;"
    print "CHOICES: set, pattern;"
    sys.exit(0)
    
def test(TestString):
    print "-------------------------------------------------------------------"
    print "expression    = \"" + TestString + "\""
    sm = core.do(TestString, {}, -1, )
    print "state machine\n", sm 

if "set" in sys.argv:
    test('[:\\C{[ﬀİ]}:]')
    test('[:\\C{[[a-z]}:]')
    test('[:\\C{[:union([a-z], [ﬀİ]):]}:]')
else:
    test('a\\C{[a-zﬀİ]}a')

# test('[:\\C{[a-z]}:]')
# test('(a|z)/c')
# test('"aac"|"bad"/"z"|congo')
# test('"aac"|"bad"|bcad')
# test("you[a-b]|[a-e]|[g-m]you")    
# test("a(a|b)*")
