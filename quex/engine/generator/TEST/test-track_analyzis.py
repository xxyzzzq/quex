#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base           import get_combined_state_machine
from   quex.engine.generator.track_analyzis import TrackInfo
from   quex.engine.generator.state_machine_decorator import StateMachineDecorator


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

dsm = StateMachineDecorator(sm, "TrackTest", 
                            PostContextSM_ID_List           = [], 
                            BackwardLexingF                 = False, 
                            BackwardInputPositionDetectionF = False)

print sm.get_string(NormalizeF=False)

ti = TrackInfo(dsm)

for state_index, state in sm.states.iteritems():
    print "State = %i" % state_index + "____________________________________"
    print state.acceptance_tracer
