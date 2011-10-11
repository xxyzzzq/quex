#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling   import *
import quex.engine.state_machine.core  as core
import quex.engine.analyzer.path.core  as paths 
from   quex.engine.analyzer.core       import Analyzer
from   quex.blackboard                 import E_EngineTypes, E_Compression

if "--hwut-info" in sys.argv:
    print "Paths: find_path (mean tests);"
    print "CHOICES: 1, 2, 3;"
    sys.exit(0)

if len(sys.argv) < 2:
    print "Call this with: --hwut-info"
    sys.exit(0)

def test(sm):
    for state_index in sm.get_orphaned_state_index_list():
        del sm.states[state_index]

    sm.add_transition(7777L, ord('0'), sm.init_state_index)
    sm.init_state_index = 7777L

    # print Skeleton
    print sm.get_graphviz_string(NormalizeF=False)
    print
    analyzer = Analyzer(sm, E_EngineTypes.FORWARD)
    result   = paths.find_begin(analyzer, 
                                sm.init_state_index, sm.init_state_index, 
                                CompressionType=E_Compression.PATH, 
                                AvailableStateIndexList=analyzer.state_db.keys())
    for path in result:
        print "# " + repr(path).replace("\n", "\n# ")

# Hint: Use 'dot' (graphviz utility) to print the graphs.
# EXAMPLE:
#          > ./paths-find_paths.py 2 > tmp.dot
#          > dot tmp.dot -Tfig -o tmp.fig       # produce .fig graph file 
#          > xfig tmp.fig                       # use xfig to view

sm = core.StateMachine()
if "1" in sys.argv: 
    """
    00007() <~ 
          == 'a' ==> 00009
          == 'b' ==> 00008
    00009(A, S) <~ (1066, 66, A, S)
    00008(A, S) <~ (10001, 66, A, S)
          == 'a' ==> 00009
          == 'b' ==> 00008
    """
    sm.init_state_index = 7L
    sm.add_transition(7L, ord('a'), 9L, AcceptanceF=True)
    sm.add_transition(7L, ord('b'), 8L, AcceptanceF=True)
    sm.add_transition(8L, ord('a'), 9L)
    sm.add_transition(8L, ord('b'), 8L)

    test(sm)

elif "2" in sys.argv: 
    """
    00014() <~ 
          == 'a' ==> 00016
          == 'b' ==> 00017
          == 'c' ==> 00015
    00016(A, S) <~ (2007, 1007, A, S)
    00017(A, S) <~ (2008, 1008, A, S)
    00015(A, S) <~ (10001, 1007, A, S), (2009, 1009, A, S)
          == 'a' ==> 00016
          == 'b' ==> 00018
          == 'c' ==> 00019
    00018(A, S) <~ (10002, 1007, A, S), (2008, 1008, A, S)
          == 'a' ==> 00016
          == 'b' ==> 00018
          == 'c' ==> 00019
    00019(A, S) <~ (2009, 1009, A, S)
    """
    sm.init_state_index = 14L
    sm.add_transition(14L, ord('a'), 16L, AcceptanceF=True)
    sm.add_transition(14L, ord('b'), 17L, AcceptanceF=True)
    sm.add_transition(14L, ord('c'), 15L, AcceptanceF=True)
    sm.add_transition(15L, ord('a'), 16L)
    sm.add_transition(15L, ord('b'), 18L)
    sm.add_transition(15L, ord('c'), 19L)
    sm.add_transition(18L, ord('a'), 16L)
    sm.add_transition(18L, ord('b'), 18L, AcceptanceF=True)
    sm.add_transition(18L, ord('c'), 19L, AcceptanceF=True)

    test(sm)

elif "3" in sys.argv: 
    """
    00010() <~ 
          == 'a' ==> 00012
          == 'b' ==> 00011
    00012(A, S) <~ (1066, 66, A, S)
    00011(A, S) <~ (10001, 66, A, S)
          == 'a' ==> 00012
          == 'b' ==> 00013
          == 'c' ==> 00011
    00013(A, S) <~ (10002, 66, A, S)
    """
    sm.init_state_index = 10L
    sm.add_transition(10L, ord('a'), 12L, AcceptanceF=True)
    sm.add_transition(10L, ord('b'), 11L, AcceptanceF=True)
    sm.add_transition(11L, ord('a'), 12L)
    sm.add_transition(11L, ord('b'), 13L, AcceptanceF=True)
    sm.add_transition(11L, ord('c'), 11L)

    test(sm)
print "#"
print "# Some recursions are possible, if the skeleton contains them."
print "# In this case, the path cannot contain but the 'iterative' char"
print "# plus some exit character."
