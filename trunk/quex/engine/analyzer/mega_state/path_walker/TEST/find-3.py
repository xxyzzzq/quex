#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling   import *
import quex.engine.state_machine.core  as core
import quex.engine.analyzer.mega_state.path.core  as paths 
from   quex.engine.analyzer.core       import Analyzer
from   quex.blackboard                 import E_EngineTypes, E_Compression

if "--hwut-info" in sys.argv:
    print "Paths: Plugging Wild Cards;"
    print "CHOICES: 1, 2, 3, 4;"
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
    for state in analyzer.state_db.itervalues():
        state.entry.door_tree_configure()
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
s0 = sm.init_state_index 

def ord2(A, B):
    return Interval(ord(A), ord(B) + 1)

if "1" in sys.argv: 
    # Wild card at 'q', before --> s1, after --> s2
    f1 = sm.add_transition(s0, ord('p'))                          #         [p]
    s1 = sm.add_transition(s0, ord2('a', 'o'), AcceptanceF=True)  # [a ... o] 
    s2 = sm.add_transition(s0, ord2('q', 'z'), AcceptanceF=True)  #           [q ... z]

    # Wild card remains
    f2 = sm.add_transition(f1, ord('p'))                          #         [p]
    sm.add_transition(f1, ord2('a', 'o'), s1)                     # [a ... o] 
    sm.add_transition(f1, ord2('q', 'z'), s2)                     #           [q ... z]

    # Wild card used 
    sm.add_transition(f2, ord('z'), AcceptanceF=True)             #                   [z]
    sm.add_transition(f2, ord2('a', 'o'), s1)                     # [a ... o] 
    sm.add_transition(f2, ord('p'),  AcceptanceF=True)            #         [p]
    sm.add_transition(f2, ord2('q', 'y'), s2)                     #           [q ... y]

    test(sm)

elif "2" in sys.argv: 
    # Wild card at 'q', before --> s1, after --> s2
    f1 = sm.add_transition(s0, ord('p'))                          #         [p]
    s1 = sm.add_transition(s0, ord2('a', 'o'), AcceptanceF=True)  # [a ... o] [q ... z] 
    no = sm.add_transition(s0, ord2('q', 'z'), s1)                #           

    # Wild card used for 'p --> s3'; path "pz" is possible
    f2 = sm.add_transition(f1, ord('z'))                          #                   [z]
    s1 = sm.add_transition(f1, ord2('a', 'o'), s1)                # [a ... o] [q ... y]
    no = sm.add_transition(f1, ord2('q', 'y'), s1)                #           
    s3 = sm.add_transition(f1, ord('p'), AcceptanceF=True)        #         [p]

    # Wild card used; "pzz" impossible because 'l' misfits
    f3 = sm.add_transition(f2, ord('z'))                          #                   [z]
    s1 = sm.add_transition(f2, ord2('a', 'k'), s1)                # [a ... k] [m ... y]
    no = sm.add_transition(f2, ord2('m', 'y'), s1)                #           
    no = sm.add_transition(f2, ord('l'), AcceptanceF=True)        #         [l]

    test(sm)

elif "3" in sys.argv: 
    # Wild card at 'q', before --> s1, after --> s2
    f1 = sm.add_transition(s0, ord('p'))                          #         [p]
    s1 = sm.add_transition(s0, ord2('a', 'o'), AcceptanceF=True)  # [a ... o] [q ... z] 
    no = sm.add_transition(s0, ord2('q', 'z'), s1)                #           

    # Wild card used for 'p --> s3'; path "pz" is possible
    f2 = sm.add_transition(f1, ord('z'))                          #                   [z]
    s1 = sm.add_transition(f1, ord2('a', 'o'), s1)                # [a ... o] [q ... y]
    no = sm.add_transition(f1, ord2('q', 'y'), s1)                #           
    s3 = sm.add_transition(f1, ord('p'), AcceptanceF=True)        #         [p]

    # Wild card used; "pzw" possible because 'p' fits
    f3 = sm.add_transition(f2, ord('w'), AcceptanceF=True)        #                   [w]
    s1 = sm.add_transition(f2, ord2('a', 'o'), s1)                # [a ... o] [q ... v] [x ... z]
    no = sm.add_transition(f2, ord2('q', 'v'), s1)                #           
    no = sm.add_transition(f2, ord2('x', 'z'), s1)                #           
    no = sm.add_transition(f2, ord('p'), s3)                      #         [p]

    test(sm)

elif "4" in sys.argv: 
    # Wild card at 'q', before --> s1, after --> s2
    f1 = sm.add_transition(s0, ord('p'))                          #         [p]
    s1 = sm.add_transition(s0, ord2('a', 'o'), AcceptanceF=True)  # [a ... o] [q ... z] 
    no = sm.add_transition(s0, ord2('q', 'z'), s1)                #           

    # Wild card used for 'p --> drop-out'; path "pz" is possible
    f2 = sm.add_transition(f1, ord('z'))                          #                   [z]
    # NOT: .add_transition(f1, ord('p'))                          #         [p]
    s1 = sm.add_transition(f1, ord2('a', 'o'), s1)                # [a ... o] [q ... y]
    no = sm.add_transition(f1, ord2('q', 'y'), s1)                #           

    # Wild card used; "pzz" impossible because 'l' misfits
    f3 = sm.add_transition(f2, ord('z'))                          #                   [z]
    s1 = sm.add_transition(f2, ord2('a', 'k'), s1)                # [a ... k] [m ... y]
    no = sm.add_transition(f2, ord2('m', 'y'), s1)                #           
    no = sm.add_transition(f2, ord('l'), AcceptanceF=True)        #         [l]

    test(sm)

print "#"
print "# Some recursions are possible, if the skeleton contains them."
print "# In this case, the path cannot contain but the 'iterative' char"
print "# plus some exit character."
