#! /usr/bin/env python
# vim: set fileencoding=utf8 :
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
from   quex.blackboard                      import setup as Setup

Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1
Setup.buffer_codec_transformation_info = "utf8-state-split"

if "--hwut-info" in sys.argv:
    print "Transformations"
    sys.exit(0)
    
def test(TestString):
    print "-------------------------------------------------------------------"
    print "expression    = \"" + TestString + "\""
    sm = core.do(TestString, {})
    print "state machine\n", sm.get_string(Option="hex") 

test('µ/µ+/µ')

