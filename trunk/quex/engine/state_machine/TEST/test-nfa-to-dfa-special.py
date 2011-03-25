#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.repeat     as repeat 
import quex.core_engine.state_machine.nfa_to_dfa as nfa_to_dfa 
## import quex.core_engine.state_machine.hopcroft_minimization as hopcroft 
import quex.input.regular_expression.engine  as core

if "--hwut-info" in sys.argv:
    print "NFA: Conversion to DFA - Special Case"
    sys.exit(0)
    
def test(RE):
    print "-------------------------------------------------------------------------------"
    print "## RE:", RE
    result = core.do(RE, {})
    ## print "## State Machine:", result
    ## result = repeat.do(result, 1)
    print "## RE+ (repetition):", result.get_string(NormalizeF=False)
    ## print result.get_graphviz_string(NormalizeF=False) 
    result = nfa_to_dfa.do(result)
    print "## NFA-to-DFA:"
    print result
    ## print result.get_graphviz_string() 
    ## print "## Hopcroft:" 
    ## print result
    ## print result.get_graphviz_string() 

test('1+a*')
test('1+[a-z]*')
test('[A-Z]*1+[a-z]*')
