#! /usr/bin/env python
# vim:fileencoding=utf8 
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
from   quex.exception import RegularExpressionException
from quex.input.setup import setup as Setup
Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Case Folding;"
    print "CHOICES: set, pattern;"
    sys.exit(0)
    
def test(TestString):
    print "-------------------------------------------------------------------"
    print "expression    = \"" + TestString + "\""
    try: 
        sm = core.do(TestString, {})
        print "state machine\n", sm 

    except RegularExpressionException, x:
        print x._message
    except:
        pass

if "set" in sys.argv:
    test('[:\\C{[ﬀİ]}:]')
    test('[:\\C{[a-z]}:]')
    test('[:\\C{[:union([a-z], [ﬀİ]):]}:]')
    test('[:\\C(m){[:union([a-z], [ﬀİ]):]}:]')
    test('[:\\C(st){[i]}:]')
    test('[:\\C(st){[I]}:]')
    test('[:\\C(st){}:]')
    test('[:\\C{[]}:]')
    test('[:\\C(d){[]}:]')
    test('[:\\C( d ){[]}:]')
    test('[:\\C( s ){[a]}:]')
else:
    test('a\\C{[a-zﬀİ]}a')
    test('a\\C(s){[a-zﬀİ]}a')
    test('a\\C(t){[a-gk-zﬀİ]}a')
    test('a\\C(t){[a-hj-zﬀİ]/}a')

