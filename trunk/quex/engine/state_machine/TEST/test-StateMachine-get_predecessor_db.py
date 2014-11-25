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
    print "CHOICES: linear, butterfly;"
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

def get_linear_state_machine(StateN):
    """Build a linear state machine, so that the predecessor states
    are simply all states with lower indices.

                  (0)--->(1)---> .... (StateN-1)
    """
    sm = StateMachine(InitStateIndex=0L)
    prev_si = 0L
    for si in xrange(1, StateN):
        si = long(si)
        sm.add_transition(prev_si, 66, si)
        prev_si = si
    return sm, StateN

def get_butterfly():
    """           
                          .-<--(4)--<---.
                         /              |
               (0)---->(1)---->(2)---->(3)---->(6)---->(7)
                         \              |
                          '-<--(5)--<---'
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(2L, 66, 3L)
    sm.add_transition(3L, 66, 4L)
    sm.add_transition(3L, 66, 5L)
    sm.add_transition(3L, 66, 6L)
    sm.add_transition(4L, 66, 1L)
    sm.add_transition(5L, 66, 1L)
    sm.add_transition(6L, 66, 7L)
    return sm, 8

def get_fork():
    """           
                          .->--(2)-->---.
                         /              |
               (0)---->(1)---->(3)---->(5)---->(6)
                         \              |
                          '->--(4)-->---'
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(1L, 66, 3L)
    sm.add_transition(1L, 66, 4L)
    sm.add_transition(2L, 66, 5L)
    sm.add_transition(3L, 66, 5L)
    sm.add_transition(4L, 66, 5L)
    sm.add_transition(5L, 66, 6L)
    return sm, 7

def get_fork2():
    """           
                          .->--(1)-->---.
                         /              |
                       (0)---->(2)---->(4)---->(5)
                         \                      |
                          '->--(3)-->-----------'
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(0L, 66, 2L)
    sm.add_transition(0L, 66, 3L)
    sm.add_transition(1L, 66, 4L)
    sm.add_transition(2L, 66, 4L)
    sm.add_transition(3L, 66, 4L)
    sm.add_transition(4L, 66, 5L)
    return sm, 6

def get_fork3():
    """           
                          .->--(2)-->--(5)
                         /              
               (0)---->(1)---->(3)---->(6)
                         \              
                          '->--(4)-->--(7)
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(1L, 66, 3L)
    sm.add_transition(1L, 66, 4L)
    sm.add_transition(2L, 66, 5L)
    sm.add_transition(3L, 66, 6L)
    sm.add_transition(4L, 66, 7L)
    return sm, 8

def get_long_loop():
    """Build a linear state machine, so that the predecessor states
    are simply all states with lower indices.

                 .--------->(5)---->-----.
                 |                       |
                (0)---->(1)---->(2)---->(6)
                 |               |
                 '--<---(4)-----(3)
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(0L, 66, 5L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(2L, 66, 3L)
    sm.add_transition(2L, 66, 6L)
    sm.add_transition(3L, 66, 4L)
    sm.add_transition(4L, 66, 0L)
    sm.add_transition(5L, 66, 6L)
    return sm, 7

def get_nested_loop():
    """           
                .--<-------(5)---<------.
                |                       |
               (0)---->(1)---->(2)---->(3)---->(4)
                        |       |   
                        '---<---'
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(2L, 66, 3L)
    sm.add_transition(2L, 66, 1L)
    sm.add_transition(3L, 66, 4L)
    sm.add_transition(3L, 66, 5L)
    sm.add_transition(5L, 66, 0L)
    return sm, 6

def get_mini_loop():
    """           
               (0)---->(1)---->(2)---->(3)
                        |       |   
                        '---<---'
    """
    sm = StateMachine(InitStateIndex=0L)
    sm.add_transition(0L, 66, 1L)
    sm.add_transition(1L, 66, 2L)
    sm.add_transition(2L, 66, 1L)
    sm.add_transition(2L, 66, 3L)
    return sm, 4

if   "linear"      in sys.argv: sm, state_n = get_linear_state_machine(7)
elif "butterfly"   in sys.argv: sm, state_n = get_butterfly()
elif "fork"        in sys.argv: sm, state_n = get_fork()
elif "fork2"       in sys.argv: sm, state_n = get_fork2()
elif "long_loop"   in sys.argv: sm, state_n = get_long_loop()
elif "nested_loop" in sys.argv: sm, state_n = get_nested_loop()
elif "mini_loop"   in sys.argv: sm, state_n = get_mini_loop()
else:                           sm, state_n = get_fork3()

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



