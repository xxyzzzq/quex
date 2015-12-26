#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from copy import deepcopy


import quex.engine.state_machine.construction.repeat as repeat
from   quex.engine.state_machine.core import *
from   quex.engine.state_machine.state.core import *
from   quex.engine.state_machine.state.single_entry import *
from   quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.algorithm.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.algorithm.hopcroft_minimization as hopcroft
import quex.engine.state_machine.check.identity as identity_checker

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


print "NOTE: '((4[a])) stands for 'state number 4 which has accepts pattern 4'"

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
set_cmd_list(sm, n1, (5555, 1, True))
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
set_cmd_list(sm, n2, (7777, 1, True))
test(sm, txt)

txt = """
          (0)---a--->((1[a]))---a--->((2[a]))
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
set_cmd_list(sm, n1, (5555, 1, True))
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
set_cmd_list(sm, n2, (5555, 1, True))
test(sm, txt)

txt = """
                                             
          (0)---a--->((1[a]))---a--->((2[a]))<--.
                                         \\       \\
                                         `----a--'
"""
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
add_origin(sm.states[n1], 5555L, 1L)
set_cmd_list(sm, n1, (5555, 1, True))
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
set_cmd_list(sm, n2, (5555, 1, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))
n3 = sm.add_transition(n1, ord('b'), AcceptanceF=True)
set_cmd_list(sm, n3, (7777L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))
n2 = sm.add_transition(n1, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))
n3 = sm.add_transition(n1, ord('b'), AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
set_cmd_list(sm, n3, (5555L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))
n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
n2 = sm.add_transition(n2, ord('a'), n2, AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))
n3 = sm.add_transition(n1, ord('b'),     AcceptanceF=False)
n3 = sm.add_transition(n3, ord('b'), n3, AcceptanceF=False)
n4 = sm.add_transition(n3, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n4, (5555L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
set_cmd_list(sm, n3, (5555L, 1L, True))

n4 = sm.add_transition(n1, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n4, (7777L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
set_cmd_list(sm, n3, (5555L, 1L, True))

n4 = sm.add_transition(n1, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n4, (5555L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
set_cmd_list(sm, n3, (5555L, 1L, True))

n4 = sm.add_transition(n2, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n4, (7777L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
set_cmd_list(sm, n3, (7777L, 1L, True))

n4 = sm.add_transition(n2, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n4, (7777L, 1L, True))
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
set_cmd_list(sm, n1, (5555L, 1L, True))

n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

n3 = sm.add_transition(n2, ord('a'),     AcceptanceF=True)
n3 = sm.add_transition(n3, ord('a'), n3, AcceptanceF=True)
set_cmd_list(sm, n3, (5555L, 1L, True))

# branch 2
n4 = sm.add_transition(n0, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n4, (5555L, 1L, True))

n5 = sm.add_transition(n4, ord('a'),     AcceptanceF=True)
n5 = sm.add_transition(n5, ord('a'), n5, AcceptanceF=True)
set_cmd_list(sm, n5, (5555L, 1L, True))

# branch 3
n6 = sm.add_transition(n0, ord('c'),     AcceptanceF=True)
n6 = sm.add_transition(n6, ord('a'), n6, AcceptanceF=True)
set_cmd_list(sm, n6, (5555L, 1L, True))

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
set_cmd_list(sm, n4, (5555L, 1L, True))

# branch 2
n5 = sm.add_transition(n0, ord('b'),     AcceptanceF=False)
n6 = sm.add_transition(n5, ord('a'),     AcceptanceF=False)
n7 = sm.add_transition(n6, ord('a'),     AcceptanceF=False)
n7 = sm.add_transition(n7, ord('a'), n7, AcceptanceF=False)
n8 = sm.add_transition(n7, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n8, (5555L, 1L, True))

# branch 3
n9  = sm.add_transition(n0, ord('c'),     AcceptanceF=True)
n9  = sm.add_transition(n9, ord('a'), n9, AcceptanceF=True)
n10 = sm.add_transition(n9, ord('b'),     AcceptanceF=True)
set_cmd_list(sm, n10, (5555L, 1L, True))

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
set_cmd_list(sm, n2, (5555L, 1L, True))

# branch 2
n1 = sm.add_transition(n0, ord('c'),     AcceptanceF=False)
n1 = sm.add_transition(n1, ord('b'), n1, AcceptanceF=False)
n2 = sm.add_transition(n1, ord('c'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

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
set_cmd_list(sm, n2, (5555L, 1L, True))

# branch 2
n1 = sm.add_transition(n0, ord('b'),     AcceptanceF=False)
n1 = sm.add_transition(n1, ord('b'), n1, AcceptanceF=False)
n2 = sm.add_transition(n1, ord('a'),     AcceptanceF=True)
set_cmd_list(sm, n2, (5555L, 1L, True))

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
set_cmd_list(sm, n2, (5555L, 1L, True))

# branch 2
n3 = sm.add_transition(n0, ord('b'),                         AcceptanceF=False)
n4 = sm.add_transition(n3, Interval(ord('a'), ord('b') + 1), AcceptanceF=True)
set_cmd_list(sm, n4, (5555L, 1L, True))

# middle branch
n4 = sm.add_transition(n1, ord('b'), n4, AcceptanceF=True)
test(sm, txt)

# post-context
txt = """
        00000()  
              == 'x' ==> 00001
        00001(S, P1) <~ 
              == 'y' ==> 00002
              == 'z' ==> 00003
        00002()  
              == 'y' ==> 00002
              == 'z' ==> 00003
        00003(A, P1)  
"""
sm = StateMachine()
n0 = sm.init_state_index
n1 = sm.add_transition(n0, ord('x'))
n2 = sm.add_transition(n1, ord('y'))
n3 = sm.add_transition(n1, ord('z'), AcceptanceF=True)
sm.add_transition(n2, ord('y'), n2)
sm.add_transition(n2, ord('z'), n3, AcceptanceF=True)
sm.states[n1].set_read_position_store_f()
test(sm, txt)

