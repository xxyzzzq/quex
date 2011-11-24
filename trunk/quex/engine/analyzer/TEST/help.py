import quex.engine.analyzer.core      as core
import quex.engine.analyzer.optimizer as optimizer
from   quex.blackboard                import E_EngineTypes, E_InputActions, setup as Setup

import sys
import os
from   operator import itemgetter

def if_DRAW_in_sys_argv(sm):
    if "DRAW" not in sys.argv: return
    fh = open("tmp.dot", "wb")
    fh.write( sm.get_graphviz_string() )
    fh.close()
    os.system("cat tmp.dot | awk ' ! /circle/ { print; }' > tmp1.dot")
    os.system("graph-easy --input=tmp1.dot --as boxart > tmp2.txt")
    os.system("awk '{ print \"   #   \", $0; }' tmp2.txt > tmp3.txt")
    os.system('echo "   #____________________________________________________________________" >> tmp3.txt')
    print "##", sys.argv[1]
    os.system('cat tmp3.txt')
    os.remove("tmp.dot")
    os.remove("tmp1.dot")
    sys.exit()

def test(SM, EngineType = E_EngineTypes.FORWARD):
    
    print SM.get_string(NormalizeF=True)

    plain     = core.Analyzer(SM, EngineType)

    # Print plain analyzer, note down what changed during optimization
    states_txt_db = {}
    for state in plain:
        if EngineType == E_EngineTypes.FORWARD:
            if state.index == SM.init_state_index: 
                assert state.input == E_InputActions.DEREF
            else:
                assert state.input == E_InputActions.INCREMENT_THEN_DEREF
        plain_txt = state.get_string(InputF=False, TransitionMapF=False)
        states_txt_db[state.index] = plain_txt
        print plain_txt

    diff_txt_db = {}
    optimized = optimizer.do(plain)
    for state in optimized:
        optimized_txt = optimized.state_db[state.index].get_string(InputF=False, TransitionMapF=False)

        if states_txt_db[state.index] != optimized_txt:
            diff_txt_db[state.index] = optimized_txt

    # Print the results of optimization
    if len(diff_txt_db):
        print 
        print "--- Optimized States ---"
        print 
        for state_index, state_txt in sorted(diff_txt_db.iteritems(), key=itemgetter(0)):
            print state_txt
