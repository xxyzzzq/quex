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

from quex.engine.state_machine.core import *
from itertools import permutations

if "--hwut-info" in sys.argv:
    print "StateMachine: get_predecessor_db;"
    print "CHOICES: linear, butterfly, long_loop, nested_loop, mini_loop, fork, fork2, fork3, fork4;"
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

def line(sm, *StateIndexSequence):
    prev_si = long(StateIndexSequence[0])
    for si in StateIndexSequence[1:]:
        si = long(si)
        sm.add_transition(prev_si, 66, si)
        prev_si = si
    return sm, len(StateIndexSequence)

def get_linear(sm):
    """Build a linear state machine, so that the predecessor states
    are simply all states with lower indices.

                  (0)--->(1)---> .... (StateN-1)
    """
    line(sm, 0, 1, 2, 3, 4, 5, 6)
    return sm, 7

def get_butterfly(sm):
    """           
                          .-<--(4)--<---.
                         /              |
               (0)---->(1)---->(2)---->(3)---->(6)---->(7)
                         \              |
                          '-<--(5)--<---'
    """
    line(sm, 0, 1, 2, 3, 6, 7)
    line(sm, 3, 4, 1)
    line(sm, 3, 5, 1)
    return sm, 8

def get_fork(sm):
    """           
                          .->--(2)-->---.
                         /              |
               (0)---->(1)---->(3)---->(5)---->(6)
                         \              |
                          '->--(4)-->---'
    """
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(1L, 66, 3L)
    sm.add_transition(1L, 66, 4L)
    sm.add_transition(2L, 66, 5L)
    sm.add_transition(3L, 66, 5L)
    sm.add_transition(4L, 66, 5L)
    sm.add_transition(5L, 66, 6L)
    return sm, 7

def get_fork2(sm):
    """           
                          .->--(1)-->---.
                         /              |
                       (0)---->(2)---->(4)---->(5)
                         \                      |
                          '->--(3)-->-----------'
    """
    line(sm, 0, 2, 4, 5)
    line(sm, 0, 3, 5)
    line(sm, 0, 1, 4)
    return sm, 6

def get_fork3(sm):
    """           
                          .->--(2)-->--(5)
                         /              
               (0)---->(1)---->(3)---->(6)
                         \              
                          '->--(4)-->--(7)
    """
    line(sm, 0, 1, 2, 5)
    line(sm, 1, 3, 6)
    line(sm, 1, 4, 7)
    return sm, 8

def get_long_loop(sm):
    """Build a linear state machine, so that the predecessor states
    are simply all states with lower indices.

                 .--------->(5)---->-----.
                 |                       |
                (0)---->(1)---->(2)---->(6)
                 |               |
                 '--<---(4)-----(3)
    """
    line(sm, 0, 1, 2, 6)
    line(sm, 2, 3, 4, 0)
    line(sm, 0, 5, 6)
    return sm, 7

def get_nested_loop(sm):
    """           
                .--<-------(5)---<------.
                |                       |
               (0)---->(1)---->(2)---->(3)---->(4)
                        |       |   
                        '---<---'
    """
    line(sm, 0, 1, 2, 3, 4)
    line(sm, 3, 5, 1)
    line(sm, 2, 1)
    return sm, 6

def get_mini_loop(sm):
    """           
               (0)---->(1)---->(2)---->(3)
                        |       |   
                        '---<---'
    """
    line(sm, 0, 1, 2, 3)
    line(sm, 2, 1)
    return sm, 4

def get_fork4(sm):
    """           
                  .->--(1)-->--(2)-->--.
                 /                      \
               (0)---->(3)---->(4)-->---(7)
                 \                      /
                  '->--(5)-->--(6)-->--'
    """
    line(sm, 0, 1, 2, 7)
    line(sm, 0, 3, 4, 7)
    line(sm, 0, 5, 6, 7)
    return sm, 8

sm = StateMachine(InitStateIndex=0L)

if   "linear"      in sys.argv: sm, state_n = get_linear(sm)
elif "butterfly"   in sys.argv: sm, state_n = get_butterfly(sm)
elif "long_loop"   in sys.argv: sm, state_n = get_long_loop(sm)
elif "nested_loop" in sys.argv: sm, state_n = get_nested_loop(sm)
elif "mini_loop"   in sys.argv: sm, state_n = get_mini_loop(sm)
elif "fork"        in sys.argv: sm, state_n = get_fork(sm)
elif "fork2"       in sys.argv: sm, state_n = get_fork2(sm)
elif "fork3"       in sys.argv: sm, state_n = get_fork3(sm)
else:                           sm, state_n = get_fork4(sm)

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



