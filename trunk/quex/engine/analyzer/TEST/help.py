import quex.engine.analyzer.core                   as     core
import quex.input.regular_expression.engine        as     regex
import quex.engine.analyzer.optimizer              as     optimizer
import quex.engine.analyzer.track_analysis         as     track_analysis
from   quex.engine.analyzer.position_register_map  import print_this
import quex.engine.analyzer.engine_supply_factory  as     engine
from   quex.engine.state_machine.engine_state_machine_set                  import get_combined_state_machine
from   quex.blackboard                             import E_InputActions, setup as Setup, E_StateIndices, E_PreContextIDs, E_Cmd

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

def prepare(PatternStringList, GetPreContextSM_F=False):
    pattern_list = map(lambda x: regex.do(x, {}), PatternStringList)
    for pattern in pattern_list:
        pattern.mount_post_context_sm()
        pattern.mount_pre_context_sm()

    if GetPreContextSM_F:
        state_machine_list = [ pattern.pre_context_sm for pattern in pattern_list ]
    else:
        state_machine_list = [ pattern.sm for pattern in pattern_list ]

    sm = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
    return sm.normalized_clone()

def test_track_analysis(SM, EngineType = engine.FORWARD, PrintPRM_F = False):
    print SM.get_string(NormalizeF=True, OriginalStatesF=False)
    from_db, to_db = SM.get_from_to_db()

    trace_db,       \
    path_element_db = track_analysis.do(SM, to_db)

    for state_index, paths_to_state in sorted(trace_db.iteritems(),key=itemgetter(0)):
        print "#State %i" % state_index
        for accept_sequence in paths_to_state:
            print accept_sequence.get_string(Indent=1)
        print

def get_drop_out_string(analyzer, StateIndex):
    txt = ".drop_out:\n"
    if_str = "if"
    for cmd in analyzer.drop_out.entry.get_command_list(E_StateIndices.DROP_OUT, StateIndex):
        if cmd.id == E_Cmd.IfPreContextSetPositionAndGoto:
            if cmd.content.pre_context_id == E_PreContextIDs.BEGIN_OF_LINE: 
                txt += "%s BeginOfLine: " % (if_str)
            elif cmd.content.pre_context_id != E_PreContextIDs.NONE: 
                txt += "%s PreContext_%s: " % (if_str, cmd.content.pre_context_id)

            if if_str == "if": if_str = "else if"
            txt += cmd.content.router_element.get_string() + "\n"
        else:
            txt += str(cmd.content) + "\n"
    return txt

def test(SM, EngineType = engine.FORWARD, PrintPRM_F = False):
    
    print SM.get_string(NormalizeF=True, OriginalStatesF=False)

    plain = core.Analyzer.from_StateMachine(SM, EngineType)

    # Print plain analyzer, note down what changed during optimization
    states_txt_db = {}
    for state in plain:
        #if EngineType.is_FORWARD():
        #    # if state.index == SM.init_state_index: assert state.input == E_InputActions.DEREF
        #    # else: assert state.input == E_InputActions.INCREMENT_THEN_DEREF
        plain_txt = state.get_string(InputF=False, TransitionMapF=False)
        states_txt_db[state.index] = plain_txt
        print plain_txt
        print get_drop_out_string(plain, state.index)

    if PrintPRM_F:
        print_this(plain)

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
            print get_drop_out_string(optimized, state_index)
