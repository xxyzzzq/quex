#! /usr/bin/env python
# vim: set fileencoding=utf8 :
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine        as core
import quex.engine.state_machine.utf8_state_split  as utf8_state_split
from   quex.engine.codec_db.core                   import CodecDynamicInfo
from   quex.blackboard                             import setup as Setup

Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1
Setup.buffer_element_specification_prepare()
Setup.buffer_codec_prepare("utf8", Module=utf8_state_split)

if "--hwut-info" in sys.argv:
    print "Transformations"
    sys.exit(0)
    
def test(TestString):
    print "-------------------------------------------------------------------"
    print "expression    = \"" + TestString + "\""
    pattern = core.do(TestString, {})

    pattern.transform(Setup.buffer_codec)
    pattern.mount_post_context_sm()
    pattern.mount_pre_context_sm()
    print "pattern\n", pattern.get_string(NormalizeF=True, Option="hex") 

test('µ/µ+/µ')
test('[aµ]+/[aµ]')
test('\Intersection{[^a] [\X0000-\U10FFFF]}+/\Intersection{[^a] [\X0000-\U10FFFF]}a')

