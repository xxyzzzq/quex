import quex.engine.state_machine.index                      as index
from   quex.engine.analyzer.core                            import Analyzer
from   quex.engine.analyzer.transition_map                  import TransitionMap
from   quex.engine.analyzer.state.core                      import AnalyzerState, Processor
from   quex.engine.analyzer.state.entry                     import Entry
from   quex.engine.analyzer.state.entry_action              import TransitionAction, \
                                                                   TransitionID
from   quex.engine.analyzer.door_id_address_label           import DoorID
import quex.engine.analyzer.engine_supply_factory           as     engine
from   quex.engine.analyzer.mega_state.core                 import MegaState
import quex.engine.analyzer.mega_state.template.core        as     templates 
from   quex.engine.analyzer.mega_state.target               import TargetByStateKey, \
                                                                   TargetByStateKey_Element
from   quex.engine.analyzer.mega_state.template.state       import TemplateState, \
                                                                   PseudoTemplateState
from   quex.engine.analyzer.mega_state.template.candidate   import TemplateStateCandidate
from   quex.engine.analyzer.commands.core                   import CommandList
from   quex.engine.analyzer.commands.tree                   import CommandTree
from   quex.engine.state_machine.core                       import State
from   quex.engine.interval_handling                        import NumberSet, Interval
from   quex.engine.tools                                    import typed

from   copy        import copy
from   operator    import attrgetter
from   collections import defaultdict
from   quex.blackboard import E_StateIndices, E_Compression, setup as Setup

import sys

def get_AnalyzerState(StateIndex, TM):
    return AnalyzerState(StateIndex, TM)

def get_AnalyzerState_Init(InitStateIndex, StateIndexList):
    init_tm = TransitionMap.from_iterable( 
        (Interval(i), state_index) 
        for i, state_index in enumerate(StateIndexList) 
    )
    return get_AnalyzerState(InitStateIndex, init_tm)

@typed(DropOutCatcher=Processor)
def get_TemplateState(State, DropOutCatcher, Name=None):
    if not isinstance(State, TemplateState): 
        State = PseudoTemplateState(State, DropOutCatcher)

    if Name is not None:
        print "State %s:" % Name, State.state_index_sequence()
        print_tm(State.transition_map, State.state_index_sequence())

    return State

def get_Analyzer(StatesDescription):
    """StatesDescription: List of pairs:
         
           (state index, transition map)

       That is, it tells what state of a given state index has what transition
       map. The transition map is a list of pairs

           (interval, target state index)
    """
    # Use 'BACKWARD_PRE_CONTEXT' so that the drop-out objects are created
    # without larger analysis.
    init_state_index = 7777L
    analyzer = Analyzer(engine.BACKWARD_PRE_CONTEXT, init_state_index)
    all_state_index_set = set()
    for state_index, transition_map in StatesDescription:
        assert isinstance(state_index, long)
        assert isinstance(transition_map, list)
        tm = TransitionMap.from_iterable(transition_map)
        tm.fill_gaps(E_StateIndices.DROP_OUT,
                     Setup.buffer_codec.drain_set.minimum(), 
                     Setup.buffer_codec.drain_set.supremum())
        analyzer.state_db[state_index] = get_AnalyzerState(state_index, tm)
        all_state_index_set.update(x[1] for x in transition_map)

    # 'Dummy' transitions from init state to all
    analyzer.state_db[init_state_index] = get_AnalyzerState_Init(init_state_index, 
                                                                 [ x[0] for x in StatesDescription ])

    # Make sure, that all states mentioned in the transition map really exist.
    for i in all_state_index_set:
        if i in analyzer.state_db: continue
        analyzer.state_db[i] = get_AnalyzerState(i, TransitionMap.from_iterable([]))

    # Make sure, that the transitions appear in the 'entry' member of the
    # states. Collect transition information.
    for state_index, transition_map in StatesDescription:
        for interval, target_index in transition_map:
            if not isinstance(target_index, (long, int)): continue
            analyzer.state_db[target_index].entry.enter(target_index, state_index, TransitionAction())
        analyzer.state_db[state_index].entry.enter(state_index, init_state_index, TransitionAction())

    for state in analyzer.state_db.itervalues():
        state.entry.categorize(state.index)

    # Make sure that every state has its entry into drop-out
    empty_cl = CommandList()
    for i in analyzer.state_db.iterkeys():
        analyzer.drop_out.entry.enter_CommandList(E_StateIndices.DROP_OUT, i, copy(empty_cl))
    analyzer.drop_out.entry.categorize(E_StateIndices.DROP_OUT)

    analyzer.prepare_DoorIDs()

    return analyzer

def get_TargetByStateKey_Element(TargetStateIndex):
    transition_id = TransitionID(TargetStateIndex, 0, 0)
    door_id       = DoorID(TargetStateIndex, 0)
    return TargetByStateKey_Element(transition_id, door_id)

def get_TargetByStateKey(TargetStateIndexList):
    scheme = [
        get_TargetByStateKey_Element(target_state_index)
        for target_state_index in TargetStateIndexList
    ]
    return TargetByStateKey.from_scheme(scheme)

def get_TransitionMap_with_TargetByStateKeys(TM_brief):
    return TransitionMap.from_iterable(
        (interval, get_TargetByStateKey(target_state_index_list))
        for interval, target_state_index_list in TM_brief
    )

def setup_TemplateState(analyzer, StateIndexList):
    assert len(StateIndexList) > 1

    s = [
        get_TemplateState(analyzer.state_db[i], analyzer.drop_out)
        for i in StateIndexList
    ]
    candidate = TemplateStateCandidate(s[0], s[1])
    result    = TemplateState(candidate)
    for state in s[2:]:
        candidate = TemplateStateCandidate(result, state) 
        result    = TemplateState(candidate)
    return result

def configure_States(TriggerMapA, StateN_A, TriggerMapB, StateN_B):
    state_setup = []
    StateListA = [ long(i) for i in xrange(StateN_A) ]
    StateListB = [ long(i) for i in xrange(StateN_A, StateN_A + StateN_B) ]
    def extract_transition_map(XTM, Index):
        result = []
        for interval, specification in XTM:
            result.append((interval, specification[Index]))
        return result

    state_setup.extend([ 
        (index.get(), extract_transition_map(TriggerMapA, i)) 
        for i, state_index in enumerate(StateListA)
    ])
    state_setup.extend([ 
        (index.get(), extract_transition_map(TriggerMapB, i)) 
        for i, state_index in enumerate(StateListB)
    ])

    analyzer = get_Analyzer(state_setup)
    if StateN_A == 1: state_a = analyzer.state_db[StateListA[0]] # Normal AnalyzerState
    else:             state_a = setup_TemplateState(analyzer, StateListA)
    if StateN_B == 1: state_b = analyzer.state_db[StateListB[0]] # Normal AnalyzerState
    else:             state_b = setup_TemplateState(analyzer, StateListB)

    return analyzer, state_a, state_b

def combine(analyzer, A, B, A_Name="A", B_Name="B", DrawF=False):
    # Make sure, that the states are 'TemplateState'-s, because the 
    # combination algo does only work on TemplateState-s.
    print "_" * 80
    A = get_TemplateState(A, analyzer.drop_out, A_Name)
    B = get_TemplateState(B, analyzer.drop_out, B_Name)
    print

    candidate = TemplateStateCandidate(A, B)
    result    = TemplateState(candidate)
    result.finalize(analyzer, CompressionType=E_Compression.TEMPLATE) # CompressionType not used for templates

    print "_ _" * 20
    print_combination_result(result, A, B, A_Name, B_Name)
    return result

def print_combination_result(combined, A, B, A_name, B_name):
    print "State %s:" % A_name, A.state_index_sequence()
    print "State %s:" % B_name, B.state_index_sequence()

    #if True:
    #    cmd_tree = CommandTree.from_AnalyzerState(combined)
    #    print "".join(cmd_tree.shared_tail_db.get_tree_text())
    print "Result:\n"
    TargetByStateKey.assign_scheme_ids(combined.transition_map)
    print_tm(combined.transition_map, combined.state_index_sequence())
    print 
    print_metric(combined.transition_map)
    print "\n"

def print_tm(TM, StateIndexList, OnlyStateIndexF=False):
    tm_str = [("  [INTERVAL]", "[SCHEME_ID]", "[TARGET/STATE %s]" % [int(x) for x in StateIndexList])]
    for interval, target in TM:
        interval_str = "  " + repr(interval).replace("%i" % sys.maxint, "oo").replace("%i" % (sys.maxint-1), "oo")
        target_str   = str(target)
        target_str   = target_str.replace("TargetByStateKey:DoorID", "**")
        target_str   = target_str.replace("TargetByStateKey:scheme", "")
        target_str   = target_str.replace("DoorID", "")
        target_str   = target_str.replace("([", "")
        target_str   = target_str.replace("])", "")
        if OnlyStateIndexF:
            target_str = target_str.replace(", d=0", "")
            target_str = target_str.replace("s=", "")
        tm_str.append((interval_str, "%s" % target.scheme_id, target_str))

    L0 = max(len(x[0]) for x in tm_str)
    L1 = max(len(x[1]) for x in tm_str)
    for interval_str, scheme_id_str, target_str in tm_str:
        print "%s%s %s%s %s" % \
              (interval_str, " " * (L0 - len(interval_str)), \
               scheme_id_str, " " * (L1-len(scheme_id_str)), \
               target_str)

def print_metric(TM):
    def get_target_scheme_list(TM):
        result = []
        for interval, target in TM:
            assert isinstance(target, TargetByStateKey)
            if target.uniform_door_id is not None: continue
            result.append(target)
        return result

    SL = get_target_scheme_list(TM)
    SL.sort(key=lambda x: tuple(x.iterable_door_id_scheme()))

    print "  BorderN = %i" % (len(TM) - 1)

