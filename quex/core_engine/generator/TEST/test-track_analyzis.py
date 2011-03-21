#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core  as regex
from   quex.core_engine.generator.base           import get_combined_state_machine
from   quex.core_engine.generator.track_analyzis import TrackInfo


if "--hwut-info" in sys.argv:
    print "Track Analyzis: Keywords 'for', 'forest', 'forester', and 'formidable'"
    sys.exit()

pattern_list = [
    'for',        
    'forest',     
]

state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)

sm = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

print sm.get_string(NormalizeF=False)

ti = TrackInfo(sm)

for state_index in sm.states.iterkeys():
    print "State = %i" % state_index
    print "    store accept.     ", ti.necessary_to_store_last_acceptance(state_index)
    print "    store accept. pos.", ti.necessary_to_store_last_acceptance_position(state_index)
    acceptance, transitions_since_acceptance = ti.acceptance_info_on_drop_out(state_index)
    print "    on drop out:       acceptance = ", acceptance
    print "                       backward   = ", transitions_since_acceptance
