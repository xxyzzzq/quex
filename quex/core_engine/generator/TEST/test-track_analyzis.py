#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core  as regex
from   quex.core_engine.generator.base           import get_combined_state_machine
from   quex.core_engine.generator.track_analyzis import TrackInfo


if "--hwut-info" in sys.argv:
    print "Track Analyzis: Necessity of storing acceptance;"
    print "CHOICES: 1, 2;"
    sys.exit()

if "1" in sys.argv:
    pattern_list = [
        'for',        
        'forest',     
    ]
elif "2" in sys.argv:
    pattern_list = [
        'aa|bca',        
        'b',     
    ]
elif "3" in sys.argv:
    pattern_list = [
        'for',        
        'for([e]+)st',     
    ]
else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)

sm = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

print sm.get_string(NormalizeF=False)

ti = TrackInfo(sm)

for state_index, state in sm.states.iteritems():
    print "State = %i" % state_index + "____________________________________"
    print state.acceptance_tracer
