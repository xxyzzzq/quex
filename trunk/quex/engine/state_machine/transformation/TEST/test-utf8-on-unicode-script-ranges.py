#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.state_machine.transformation.utf8_state_split import EncodingTrafoUTF8
from   quex.engine.state_machine.transformation.utf8_state_split import unicode_to_utf8
from   quex.engine.state_machine.transformation.TEST.helper      import test_on_UCS_sample_sets

if "--hwut-info" in sys.argv:
    print "UTF8 Split: Unicode Language-Scripts as Examplary Ranges"
    sys.exit()

test_on_UCS_sample_sets(EncodingTrafoUTF8(), unicode_to_utf8)

