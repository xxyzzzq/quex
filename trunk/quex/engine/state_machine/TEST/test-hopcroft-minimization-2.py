#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from copy import deepcopy


import quex.engine.state_machine.repeat as repeat
from   quex.engine.state_machine.core import *
from   quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.hopcroft_minimization as hopcroft
import quex.engine.state_machine.identity_checker as identity_checker

if "--hwut-info" in sys.argv:
    print "DFA: Hopcroft optimization (minimize state set) II"
    print "CHOICES: NEW, ADAPT;"
    print "SAME;"
    sys.exit(0)

if "NEW" in sys.argv:     CreateNewStateMachineF=True
elif "ADAPT" in sys.argv: CreateNewStateMachineF=False
else:
    print "Require command line arguments: '--hwut-info', 'NEW', or 'ADAPT'"
    sys.exit(-1)


print "NOTE: '((4[a])) stands for 'state number 4 which has origin pattern 4'"

test_i = 0
def test(sm, txt):
    global test_i
    backup_sm = deepcopy(sm)
    print "_______________________________________________________________________________"
    print ("(%i)" % test_i),
    print txt
    optimal_sm = hopcroft.do(sm, CreateNewStateMachineF=CreateNewStateMachineF)
    print optimal_sm
    test_i += 1
    orphan_state_index_list = optimal_sm.get_orphaned_state_index_list()
    if len(orphan_state_index_list) != 0:
        print "ERROR: orphan states found = ", orphan_state_index_list
    if identity_checker.do(backup_sm, optimal_sm) == False:
        print "ERROR: state machines not equivalent"

txt = """
          (0)---a--->((1[a]))---a--->((2[b]))

          where 'a' and 'b' are different origins
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
sm.states[n2].add_origin(7777L, 1L)
test(sm, txt)

txt = """
          (0)---a--->((1[a]))---a--->((2[a]))
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)
test(sm, txt)

txt = """
                                             
          (0)---a--->((1[a]))---a--->((2[a]))<--.
                                         \\       \\
                                         `----a--'
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)
test(sm, txt)


txt = """
          (0)---a--->((1[a]))---a--->((2[a]))<--.
                         \\              \\        \\
                          \\              `----a--'
                           `--b----->((3[b]))
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)
n3 = sm.add_transition(n1, ord('b'), AcceptanceF=True)
sm.states[n3].add_origin(7777L, 1L)
test(sm, txt)


txt = """
          (0)---a--->((1[a]))---a--->((2[a]))<--.
                         \\              \\        \\
                          \\              `----a--'
                           `--b----->((3[a]))<--.
                                         \\        \\
                                          `----a--'
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)
n3 = sm.add_transition(n1, ord('b'), AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
sm.states[n3].add_origin(5555L, 1L)
test(sm, txt)


txt = """
          (0)---a--->((1[a]))---a--->((2[a]))<--.
                         \\              \\        \\
                          \\              `----a--'
                           `--b----->(3)<-------.
                                      | \\        \\
                                      a  `----b--'
                                      |
                                   ((4[a]))
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)
n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)
n3 = sm.add_transition(n1, ord('b'),     AcceptanceF=False)
n3 = sm.add_transition(n3, ord('b'), n3, AcceptanceF=False)
n4 = sm.add_transition(n3, ord('a'),     AcceptanceF=True)
sm.states[n4].add_origin(5555L, 1L)
test(sm, txt)


txt = """
          (0)---a--->((1[a]))---a--->((2[a]))---a--->((3[a]))<--.
                         \\                              \\        \\
                          \\                              `----a--'
                           `--b----->((4[b]))
"""
sm = StateMachine()
n0 = sm.init_state_index     

n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
sm.states[n3].add_origin(5555L, 1L)

n4 = sm.add_transition(n1, ord('b'),     AcceptanceF=True)
sm.states[n4].add_origin(7777L, 1L)
test(sm, txt)

txt = """
          (0)---a--->((1[a]))---a--->((2[a]))---a--->((3[a]))<--.
                         \\                              \\        \\
                          \\                              `----a--'
                           `--b----->((4[a]))
"""
sm = StateMachine()
n0 = sm.init_state_index     

n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
sm.states[n3].add_origin(5555L, 1L)

n4 = sm.add_transition(n1, ord('b'),     AcceptanceF=True)
sm.states[n4].add_origin(5555L, 1L)
test(sm, txt)

txt = """
          (0)---a--->((1[a]))---a--->((2[a]))---a--->((3[a]))<--.
                                         \\              \\        \\
                                          \\              `----a--'
                                           `--b----->((4[b]))
"""
sm = StateMachine()
n0 = sm.init_state_index     

n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
sm.states[n3].add_origin(5555L, 1L)

n4 = sm.add_transition(n2, ord('b'),     AcceptanceF=True)
sm.states[n4].add_origin(7777L, 1L)
test(sm, txt)

txt = """
          (0)---a--->((1[a]))---a--->((2[a]))---a--->((3[b]))<--.
                                         \\              \\        \\
                                          \\              `----a--'
                                           `--b----->((4[b]))
"""
sm = StateMachine()
n0 = sm.init_state_index     

n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
sm.states[n3].add_origin(7777L, 1L)

n4 = sm.add_transition(n2, ord('b'),     AcceptanceF=True)
sm.states[n4].add_origin(7777L, 1L)
test(sm, txt)


txt = """
          (0)---a--->((1[a]))---a--->((2[a]))---a--->((3[a]))<--.
           |\\                                           \\        \\
           | \\                                           `----a--'
           |  b                                              
           |   '---->((4[a]))---a--->((5[a]))<--.
           .                            \\        \\
            \\                            `----a--'
              c                                              
               '---->((3[a]))<--.
                        \\        \\
                         `----a--'
"""
sm = StateMachine()
n0 = sm.init_state_index     

# branch 1
n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=True)
sm.states[n1].add_origin(5555L, 1L)

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
sm.states[n3].add_origin(5555L, 1L)

# branch 2
n4 = sm.add_transition(n0, ord('b'),     AcceptanceF=True)
sm.states[n4].add_origin(5555L, 1L)

n5 = sm.add_transition(n4, ord('a'),     AcceptanceF=True)
n5 = sm.add_transition(n5, ord('a'), n5, AcceptanceF=True)
sm.states[n5].add_origin(5555L, 1L)

# branch 3
n6 = sm.add_transition(n0, ord('c'),     AcceptanceF=True)
n6 = sm.add_transition(n6, ord('a'), n6, AcceptanceF=True)
sm.states[n6].add_origin(5555L, 1L)

test(sm, txt)


txt = """
          (0)---a--->(1)---a--->(2)---a--->(3)<--. ---b-->((4[a]))
           |\\                               \\     \\
           | \\                               `--a--'
           |  b                                              
           |   '---->(5)---a--->(6)---a--->(7)<--. ---b-->((8[a]))
           .                                 \\     \\
            \\                                `--a--'
              c                                              
               '---->(9)<--. ---b-->((10[a]))
                      \\     \\
                       `--a--'
"""
sm = StateMachine()
n0 = sm.init_state_index     

# branch 1
n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=False)
n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=False)
n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=False)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=False)
n4 = sm.add_transition(n3, ord('b'),     AcceptanceF=True)
sm.states[n4].add_origin(5555L, 1L)

# branch 2
n5 = sm.add_transition(n0, ord('b'),     AcceptanceF=False)
n6 = sm.add_transition(n5, ord('a'),     AcceptanceF=False)
n7 = sm.add_transition(n6, ord('a'),     AcceptanceF=False)
n7 = sm.add_transition(n7, ord('a'), n7, AcceptanceF=False)
n8 = sm.add_transition(n7, ord('b'),     AcceptanceF=True)
sm.states[n8].add_origin(5555L, 1L)

# branch 3
n9  = sm.add_transition(n0, ord('c'),     AcceptanceF=True)
n9  = sm.add_transition(n9, ord('a'), n9, AcceptanceF=True)
n10 = sm.add_transition(n9, ord('b'),     AcceptanceF=True)
sm.states[n10].add_origin(5555L, 1L)

test(sm, txt)



txt = """
          (0)---b-->(1)<---.----b-->((2[a]))
            \\        \\      \\        
             \\        `--c--'             
              `-c-->(3)<---.---c-->((4[a]))
                      \\     \\        
                       `--b--'             
                                    
"""
sm = StateMachine()
n0 = sm.init_state_index     

# branch 1
n1 = sm.add_transition(n0, ord('b'),     AcceptanceF=False)
n1 = sm.add_transition(n1, ord('c'), n1, AcceptanceF=False)
n2 = sm.add_transition(n1, ord('b'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

# branch 2
n1 = sm.add_transition(n0, ord('c'),     AcceptanceF=False)
n1 = sm.add_transition(n1, ord('b'), n1, AcceptanceF=False)
n2 = sm.add_transition(n1, ord('c'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

test(sm, txt)

txt = """
          (0)---a--->(1)---a--->((4[a]))
             \\     
              b                         
               '---->(5)<---.---a--->((8[a]))
                      \\      \\
                       `--b--'
"""
sm = StateMachine()
n0 = sm.init_state_index     

# branch 1
n1 = sm.add_transition(n0, ord('a'),     AcceptanceF=False)
n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

# branch 2
n1 = sm.add_transition(n0, ord('b'),     AcceptanceF=False)
n1 = sm.add_transition(n1, ord('b'), n1, AcceptanceF=False)
n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

test(sm, txt)

txt = """

        ( 0 )-- a -->( 1 )-- a --> (( 2 ))
           \\           \\
            b             b                    (( 2 )) and (( 4 )) accept the same     
             \\            '-------\\
              '-->( 3 )-- [ab] --> (( 4 )) 
"""
sm = StateMachine()
n0 = sm.init_state_index     

# branch 1
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=False)
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
sm.states[n2].add_origin(5555L, 1L)

# branch 2
n3 = sm.add_transition(n0, ord('b'),                         AcceptanceF=False)
n4 = sm.add_transition(n3, Interval(ord('a'), ord('b') + 1), AcceptanceF=True)
sm.states[n4].add_origin(5555L, 1L)

# middle branch
n4 = sm.add_transition(n1, ord('b'), n4, AcceptanceF=True)
test(sm, txt)

