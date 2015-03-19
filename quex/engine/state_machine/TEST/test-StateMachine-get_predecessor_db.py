#! /usr/bin/env python
#
# PURPOSE: The function 'get_predecessor_db' iterates over the states of the
#          state machine by 'iteritems()'. This test makes sure, that the 
#          predecessors are always caught, independent of the sequence in which
#          the states occur.
# 
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import sys
import os
from copy import copy
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import *
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from itertools                                                  import permutations

if "--hwut-info" in sys.argv:
    print "StateMachine: get_predecessor_db;"
    print "CHOICES: %s;" % get_sm_shape_names()
    sys.exit(0)

class MyStates(dict):
    """A dictionary to represent the state machine's '.states' member
    but it iterates over the items in a manner described by 'Sequence'.
    """
    constructor_call_n = 0
    sequence_set       = set()
    def __init__(self, OriginalStates, Sequence):
        dict.__init__(copy(OriginalStates))
        self.__list     = sorted(dict.items(OriginalStates))
        self.__sequence = Sequence
        self.iteritems_call_count_n  = 0 # Double check, that 'iteritems()' has been called.
        MyStates.constructor_call_n += 1

    def iteritems(self):
        # Make sure, that no sequence appears twice
        assert sequence not in MyStates.sequence_set
        MyStates.sequence_set.add(sequence)

        for i in self.__sequence:
            self.iteritems_call_count_n += 1
            yield self.__list[i]

sm, state_n, pic = get_sm_shape_by_name(sys.argv[1])
if "pic" in sys.argv:
    print pic

base = range(state_n)

original_states   = sm.states
prototype         = None
prototype_iteritems_call_count_n = None
for sequence in permutations(base, state_n):
    sm.states = MyStates(original_states, sequence)
    result    = sm.get_predecessor_db()
    if sm.states.iteritems_call_count_n == -1:
        print "get_predecessor_db() did not call 'iteritems()'"
        print "TEST ARE NOT VALID!"
        sys.exit()
    elif state_n != sm.states.iteritems_call_count_n:
        print "ERROR: A different number of iterations happend"
        sys.exit()
    elif prototype is None: 
        prototype         = result
    elif prototype != result:
        print "ERROR: predecessor database differed"
        sys.exit()

print "PredecessorDb (for all %i permutations):" % MyStates.constructor_call_n
for si, predecessors in sorted(prototype.iteritems()):
    print ("%i -> %s" % (si, list(predecessors))).replace("L", "")



