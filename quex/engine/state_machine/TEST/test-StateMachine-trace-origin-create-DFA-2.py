#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.state_machine.core import *
import quex.input.regular_expression.engine as regex
import quex.engine.state_machine.algorithm.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.construction.parallelize as parallelize

if "--hwut-info" in sys.argv:
    print "Tracing origin: NFA to DFA (subset construction) II"
    sys.exit(0)
    
sm1 = regex.do('[A-Z]+', {}).sm
sm2 = regex.do('"PR"', {}).sm

# (*) create the DFA from the specified NFA
sm1.mark_state_origins()
sm2.mark_state_origins()

print "## sm1 = ", sm1.get_string(OriginalStatesF=False, NormalizeF=True)
print "## sm2 = ", sm2.get_string(OriginalStatesF=False, NormalizeF=True)

sm = parallelize.do([sm1, sm2])

print "## parallelized:", sm.get_string(NormalizeF=True, OriginalStatesF=False)
# print "## parallelized:", sm.get_string(NormalizeF=False)

dfa = nfa_to_dfa.do(sm)
print dfa.get_string(OriginalStatesF=False, NormalizeF=True)

