#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as re2sm
import quex.engine.utf8                    as utf8
from quex.input.setup import setup as Setup
Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "State Machine Pattern Matching"
    sys.exit(0)

def test(the_state_machine, string_to_match):
    """Uses the given state machine to match against the 'string_to_match'."""
    print
    print "string = ", string_to_match
    letter_code_list = utf8.map_n_utf8_to_unicode(string_to_match)
    state_index = the_state_machine.init_state_index
    letter_n = -1
    for letter_code in letter_code_list:   
        letter_n += 1   
        if letter_n % 5 == 0: sys.stdout.write("\n")
        state_index = sm.states[state_index].transitions().get_resulting_target_state_index(letter_code) 
        sys.stdout.write("'%s' --> (%s), " % (utf8.map_unicode_to_utf8(letter_code), 
                                             repr(state_index).replace("L","")))
        if state_index == -1: break

    print

print "_____________________________________________________________________________"    
regex_str = "h[alowe ]+t"
print "regular expression = '%s'" % regex_str
sm = re2sm.do(regex_str, {})
print sm
test(sm, "hallo welt")    
test(sm, "haaawwwolellewat")    

print "_____________________________________________________________________________"    
regex_str = "a+(b|c)*t"
print "regular expression = '%s'" % regex_str
sm = re2sm.do(regex_str, {})
print sm
test(sm, "aaaacccbbt")    
test(sm, "abcbcbct")    
