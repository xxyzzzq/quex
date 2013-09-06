import quex.engine.state_machine.index                      as index
from   quex.engine.analyzer.state.core                      import AnalyzerState
from   quex.engine.analyzer.state.entry                     import Entry
from   quex.engine.analyzer.state.entry_action              import DoorID
import quex.engine.analyzer.engine_supply_factory           as     engine
from   quex.engine.analyzer.mega_state.core                 import MegaState
import quex.engine.analyzer.mega_state.template.core        as templates 
from   quex.engine.analyzer.mega_state.template.state       import TargetByStateKey, TemplateState, PseudoTemplateState
from   quex.engine.analyzer.mega_state.template.candidate   import TemplateStateCandidate
import quex.engine.generator.state.entry_door_tree          as     entry_door_tree
from   quex.engine.state_machine.core                       import State
from   quex.engine.interval_handling                        import NumberSet, Interval

from   operator    import attrgetter
from   collections import defaultdict

import sys

def setup_sm_state(StateIndex, TM):
    result = State(StateIndex=StateIndex)
    transition_map = defaultdict(NumberSet)
    for interval, target in TM:
        transition_map[target].unite_with(interval)
    result.target_map.clear(transition_map)
    return result

def setup_AnalyzerStates(StatesDescription):
    assert isinstance(StatesDescription, list)
    for state_index, transition_map in StatesDescription:
        assert isinstance(state_index, long)
        assert isinstance(transition_map, list)

    requested_state_index_list = [ x[0] for x in StatesDescription ]

    # Use 'BACKWARD_PRE_CONTEXT' so that the drop-out objects are created
    # without larger analyzsis.
    EngineType     = engine.BACKWARD_PRE_CONTEXT

    # Pseudo transitions from init state to all
    InitStateIndex = 7777L
    init_tm        = [ (Interval(i, i+1), state_index) for i, state_index in enumerate(requested_state_index_list) ]
    init_state     = setup_sm_state(InitStateIndex, init_tm)
    sm_state_db    = dict((state_index, setup_sm_state(long(state_index), tm)) for state_index, tm in StatesDescription)
    analyzer       = TestAnalyzer(engine.BACKWARD_PRE_CONTEXT)

    # Make sure, that the transitions appear in the 'entry' member of the
    # states. Collect transition information.
    transition_db = defaultdict(list)
    for state_index, transition_map in StatesDescription:
        for interval, target_index in transition_map:
            if not isinstance(target_index, (long,int)): continue
            transition_db[target_index].append(state_index)
        transition_db[state_index].append(InitStateIndex)

    # Setup the states with their 'from_state_list'
    InitState  = AnalyzerState.from_State(init_state, InitStateIndex, True, EngineType, set())
    for state_index, from_state_list in transition_db.iteritems():
        sm_state = sm_state_db.get(state_index)
        if sm_state is None: sm_state = setup_sm_state(state_index, [])
        analyzer.state_db[state_index] = AnalyzerState.from_State(sm_state, state_index, False, EngineType, set(from_state_list))

    for state in analyzer.state_db.itervalues():
        state.entry.action_db.categorize(state.index)
    for state in analyzer.state_db.itervalues():
        state.transition_map = state.transition_map.relate_to_door_ids(analyzer, state.index)

    # Repplace all states with a pseudo MegaState
    #for state in analyzer.state_db.values():
    #    analyzer.state_db[state.index] = PseudoTemplateState(state)

    return analyzer

def setup_TemplateState(analyzer, StateIndexList):
    assert len(StateIndexList) > 1

    candidate = TemplateStateCandidate(analyzer.state_db[StateIndexList[0]], 
                                       analyzer.state_db[StateIndexList[1]]) 
    result    = TemplateState(candidate)
    for i in StateIndexList[2:]:
        candidate = TemplateStateCandidate(result, analyzer.state_db[i]) 
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

    state_setup.extend([ (index.get(), extract_transition_map(TriggerMapA, i)) for i, state_index in enumerate(StateListA)])
    state_setup.extend([ (index.get(), extract_transition_map(TriggerMapB, i)) for i, state_index in enumerate(StateListB)])

    analyzer = setup_AnalyzerStates(state_setup)
    if StateN_A == 1: state_a = analyzer.state_db[StateListA[0]] # Normal AnalyzerState
    else:             state_a = setup_TemplateState(analyzer, StateListA)
    if StateN_B == 1: state_b = analyzer.state_db[StateListB[0]] # Normal AnalyzerState
    else:             state_b = setup_TemplateState(analyzer, StateListB)

    return analyzer, state_a, state_b

def test_combination(StateA, StateB, analyzer, StateA_Name="A", StateB_Name="B", DrawF=False, FinalizeF=True):
    print
    if not isinstance(StateA, MegaState): 
        StateA = PseudoTemplateState(StateA)
    print "State%s:" % StateA_Name, StateA.state_index_sequence()
    print_tm(StateA.transition_map, StateA.state_index_sequence())

    if not isinstance(StateB, MegaState): 
        StateB = PseudoTemplateState(StateB)
    print "State%s:" % StateB_Name, StateB.state_index_sequence()
    print_tm(StateB.transition_map, StateB.state_index_sequence())

    print
    candidate = TemplateStateCandidate(StateA, StateB)
    result    = TemplateState(candidate)
    result.finalize(analyzer) # entry.action_db.categorize(result.index)
    # result.transition_map = result.transition_map.relate_to_door_ids(analyzer, result.index)

    if DrawF:
        door_tree_root = entry_door_tree.do(result.index, result.entry.action_db)
        print "DoorTree(%s|%s):" % (StateA_Name, StateB_Name)
        print "    " + door_tree_root.get_string(result.entry.action_db).replace("\n", "\n    ")
    print "Result"

    #for state_index in result.implemented_state_index_set():
    #    analyzer.state_db[state_index] = AbsorbedState(analyzer.state_db[state_index], 
    #                                                   result)

    #if FinalizeF:
    #    result.transition_map.relate_to_door_ids(analyzer.state_db)

    print_tm(result.transition_map, result.state_index_sequence())
    print_metric(result.transition_map)
    print
    print
    return result

class TestAnalyzer:
    def __init__(self, EngineType):
        self.state_db = {}
        self.__engine_type = EngineType

    @property
    def engine_type(self): 
        return self.__engine_type

def scheme_str(X):
    if X.scheme is not None: 
        return str(X.scheme).replace("L", "")
    elif X.door_id is not None:
        return "door(s%sd%s)" % (X.door_id.state_index, X.door_id.door_index)
    elif X.recursive_f:
        return "recurse"
    elif X.drop_out_f:
        return "drop_out"
    else:
        return "<<error>>"

def __TargetByStateKey_print(ego, PrintDoorsF=False, FrameF=True):
    prefix  = "MST:"
    content = ""
    suffix  = "" 

    if   ego.drop_out_f:          
        content  = "DropOut"

    elif ego.uniform_door_id is not None: 
        if PrintDoorsF: target = ego.uniform_door_id
        else:           target = ego.uniform_door_id.state_index
        prefix  += "("
        content  = repr(target).replace("L", "")
        suffix   = ")"

    else:
        if PrintDoorsF: scheme = [x for x in ego.iterable_door_id_scheme()]
        else:           scheme = tuple(door_id.state_index for door_id in ego.iterable_door_id_scheme())
        prefix  += "scheme("
        content  = repr(scheme).replace("L", "")
        suffix   = ")"

    if FrameF:
        return prefix + content + suffix
    else:
        return content

def print_tm(TM, StateIndexList):
    tm_str = [("  [INTERVAL]", "[TARGET/STATE %s]" % [int(x) for x in StateIndexList])]
    for interval, target in TM:
        interval_str = "  " + repr(interval).replace("%i" % sys.maxint, "oo").replace("%i" % (sys.maxint-1), "oo")
        target_str   = __TargetByStateKey_print(target)
        tm_str.append((interval_str, target_str))

    L = max(len(x[0]) for x in tm_str)
    for interval_str, target_str in tm_str:
        print "%s%s   %s" % (interval_str, " " * (L - len(interval_str)), target_str)

def OLD_print_tm(TM):
    """Prints a trigger map. That is, character ranges are aligned horizontally, 
       and target states, or respectively involved state lists are printed 
       inside the cells. E.g.

       |         |         |         |        |    [1L, 2L, 3L], 1, [7L, 4L, 3L], 7;

       Means, that there are four intervals. The first is a TemplateCombination
       and triggers to '[1, 2, 3]', the second is a pure state and triggers to 
       state '1', the third is a TemplateCombination and triggers to '[7, 4, 3]'
       and the forth interval triggers to '7'.

       NOTE: The first state in an involved state list is always state index of 
             the TemplateCombination. 
    """
    cursor = 0
    txt    = [" "] * 40
    for info in TM[1:]:
        x = max(0, min(40, info[0].begin))
        txt[x] = "|"

    txt[0]  = "|"
    txt[39] = "|"
    print "".join(txt),

    txt = ""
    last_i = len(TM) - 1
    for i, info in enumerate(TM):
        if not isinstance(info[1], TargetByStateKey): 
            txt += "%s" % repr(info[1]).replace("L", "")
        else: 
            txt += "%s" % scheme_str(info[1])
        if i != last_i: txt += ", "

    txt += ";"
    print "   " + txt

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

    print "BorderN        = %i" % (len(TM) - 1)
   
    tc_str = ""
    last_i = len(SL) - 1
    for i, mst in enumerate(SL):
        tc_str += "%s" % __TargetByStateKey_print(mst, FrameF=False)
        if i != last_i: tc_str += ", "
    print "Target Schemes = %s" % tc_str

