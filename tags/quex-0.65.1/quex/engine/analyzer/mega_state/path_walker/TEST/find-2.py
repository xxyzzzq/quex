#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling   import *
import quex.engine.state_machine.core  as core
import quex.engine.analyzer.mega_state.path_walker.core  as paths 
import quex.engine.analyzer.engine_supply_factory      as     engine
from   quex.engine.analyzer.core       import Analyzer
from   quex.blackboard                 import E_Compression

from   helper import find_core

if "--hwut-info" in sys.argv:
    print "Paths: find_path (mean tests);"
    print "CHOICES: 1, 2, 3, 4a, 4b;"
    sys.exit(0)

if len(sys.argv) < 2:
    print "Call this with: --hwut-info"
    sys.exit(0)

def test(sm, SelectF=False):
    for state_index in sm.get_orphaned_state_index_list():
        del sm.states[state_index]

    sm.add_transition(7777L, ord('0'), sm.init_state_index)
    sm.init_state_index = 7777L

    # print Skeleton
    result = find_core(sm, SelectF)

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

else:
    def state_index_by_node(LayerIndex, NodeIndex, NodeNperLayer):
        return long((NodeIndex + LayerIndex * NodeNperLayer) + 1)

    def setup_fork(sm, LayerN, NodeNperLayer):
        """Generate a larger grid where all would allow a path:

                    .--( )--a-->( )--a-->( )--a-->( )
                 ( )---( )--a-->( )--a-->( )--a-->( )
                    '--( )--a-->( )--a-->( )--a-->( )

        """
        sm.init_state_index = 0L
        # Generate the states.
        for layer_i in xrange(LayerN):
            for node_i in xrange(NodeNperLayer):
                # Only the nodes at the end 'accept'
                acceptance_f = (node_i == NodeNperLayer - 1)
                sm.create_new_state(acceptance_f, state_index_by_node(layer_i, node_i, NodeNperLayer))
            # Let each state at the end be a different acceptance state
            state_index = state_index_by_node(layer_i, NodeNperLayer - 1, NodeNperLayer)
            sm.states[state_index].mark_self_as_origin(AcceptanceID=long(layer_i), StateIndex=state_index) 

        for layer_i in xrange(LayerN):
            # Fork into the different lines 
            target_state_index = state_index_by_node(layer_i, 0, NodeNperLayer)
            sm.add_transition(sm.init_state_index, ord('A') + layer_i, target_state_index)
            # Generate transitions along the lines (all on 'a')
            for node_i in xrange(NodeNperLayer - 1):
                state_index                   = state_index_by_node(layer_i, node_i, NodeNperLayer)
                straight_follower_state_index = state_index_by_node(layer_i, node_i + 1, NodeNperLayer)
                print "# %s ----> %s" % (state_index, straight_follower_state_index)
                sm.add_transition(state_index, ord('a'), straight_follower_state_index)

    def create_common_nucleus(sm, LayerN, NodeNperLayer):
        NodeN               = LayerN * NodeNperLayer
        nucleus_state_index = long(NodeN + 1)
        for layer_i in xrange(LayerN):
            for node_i in xrange(NodeNperLayer - 1):
                state_index = state_index_by_node(layer_i, node_i, NodeNperLayer)
                sm.add_transition(state_index, ord('b'), nucleus_state_index, AcceptanceF=True)

    #        def add_common_transitions(sm, StateIndex, NodeN):
    #            for node_id in xrange(NodeN, NodeN*2):
    #                character          = ord('b') + node_id
    #                target_state_index = long(node_id + 1)
    #                sm.add_transition(StateIndex, character, target_state_index)
    #    for layer_i in xrange(LayerN):
    #        for node_i in xrange(NodeNperLayer-1):
    #            add_common_transitions(sm, layer_i, node_i, node_n)
    if "4a" in sys.argv:
        setup_fork(sm, 5, 5)
    elif "4b" in sys.argv:
        setup_fork(sm, 5, 5)
        create_common_nucleus(sm, 5, 5)
    elif "4c" in sys.argv:
        setup_fork(sm, 5, 50)
        create_common_nucleus(sm, 5, 50)
    test(sm, SelectF=True)
    print "#DONE"

print "#"
print "# Some recursions are possible, if the skeleton contains them."
print "# In this case, the path cannot contain but the 'iterative' char"
print "# plus some exit character."
