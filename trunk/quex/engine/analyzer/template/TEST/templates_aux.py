import quex.engine.analyzer.template.core      as templates 
from   quex.engine.analyzer.core               import AnalyzerState
from   quex.engine.analyzer.state_entry        import Entry
from   quex.engine.analyzer.state_entry_action import DoorID
from   quex.engine.analyzer.template.state     import TargetScheme, TemplateState
from   quex.engine.state_machine.core          import State
from   quex.engine.interval_handling           import NumberSet, Interval
from   quex.blackboard                         import E_EngineTypes
from   operator import attrgetter
from   collections import defaultdict

def setup_sm_state(StateIndex, TM):
    result = State(StateIndex=StateIndex)
    transition_map = defaultdict(NumberSet)
    for interval, target in TM:
        transition_map[target].unite_with(interval)
    result.transitions().clear(transition_map)
    return result

def setup_AnalyzerStates(StateAIndex, TMa, StateBIndex, TMb):
    # Use 'BACKWARD_PRE_CONTEXT' so that the drop-out objects are created
    # without larger analyzsis.
    EngineType = E_EngineTypes.BACKWARD_PRE_CONTEXT

    InitStateIndex = 7777L
    init_state = setup_sm_state(InitStateIndex, 
                                [ (Interval(1,2), StateAIndex), 
                                  (Interval(2,3), StateBIndex) ])

    sm_state_a = setup_sm_state(StateAIndex, TMa)
    sm_state_b = setup_sm_state(StateBIndex, TMb)

    analyzer = TestAnalyzer()

    # Make sure, that the transitions appear in the 'entry' member of the states.
    # -- collect transition information
    transition_db = defaultdict(list)
    for state_index in collect_target_state_indices(TMa):
        transition_db[state_index].append(StateAIndex)
    for state_index in collect_target_state_indices(TMb):
        transition_db[state_index].append(StateBIndex)
    transition_db[StateAIndex].append(InitStateIndex)
    transition_db[StateBIndex].append(InitStateIndex)

    # -- setup the states with their 'from_state_list'
    for state_index, from_state_list in transition_db.iteritems():
        if state_index in [StateAIndex, StateBIndex]: continue
        sm_state = setup_sm_state(state_index, [])
        state    = AnalyzerState(sm_state, state_index, False, EngineType, from_state_list)
        analyzer.state_db[state_index] = state

    InitState = AnalyzerState(init_state, InitStateIndex, True, EngineType, [])

    StateA = AnalyzerState(sm_state_a, StateAIndex, False, 
                           EngineType, transition_db[StateAIndex])
    StateB = AnalyzerState(sm_state_b, StateBIndex, False, 
                           EngineType, transition_db[StateBIndex])

    analyzer.state_db[InitStateIndex] = InitState 
    analyzer.state_db[StateAIndex] = StateA 
    analyzer.state_db[StateBIndex] = StateB

    for state in analyzer.state_db.itervalues():
        state.entry.door_tree_configure()

    return StateA, StateB, analyzer

def collect_target_state_indices(TM):
    result = set()
    for interval, target in TM:
        if isinstance(target, (int, long)): result.add(target)
    return result

def clean_transition_map(tm):
    for i, element in enumerate(tm):
        x = element[1]
        if isinstance(element[1], list): 
            x = tuple(DoorID(x, 0) for x in element[1])
        tm[i] = (element[0], TargetScheme(x, 0))

class TestAnalyzer:
    def __init__(self, *StateList):
        self.state_db = {}
        for element in StateList:
            if isinstance(element, list):
                for state in element:
                    self.state_db[state.index] = state
            else:
                self.state_db[element.index] = element

class TestTemplateState(TemplateState):
    def __init__(self, TriggerMap, StateIndexList):
        self.__transition_map   = TriggerMap
        clean_transition_map(self.__transition_map)
        self.__state_index_list = StateIndexList
        self.entry              = Entry(0, [])

    @property 
    def transition_map(self): 
        return self.__transition_map
    @property
    def state_index_list(self): 
        return self.__state_index_list
    @property
    def index(self): 
        return None

def get_combination(TriggerMap, StateList):
    """Creates A Template Combination Object for the given Trigger Map
       and States. The trigger map is a list of objects

            [ interval, State Index to which interval triggers ] 

       The generated object of type 'TemplateCombination' will contain
       the 'StateList' as '__involved_state_list' and the trigger map
       as '__trigger_map'.
    """

    result = templates.TemplateCombination(map(long, StateList), [])

    for info in TriggerMap: 
        result.append(info[0].begin, info[0].end, info[1])

    return result

def scheme_str(X):
    if X.scheme is not None: 
        return str(tuple(x.state_index for x in X.scheme)).replace("L", "")
    elif X.door_id is not None:
        return "door(s%sd%s)" % (X.door_id.state_index, X.door_id.door_index)
    elif X.recursive_f:
        return "recurse"
    elif X.drop_out_f:
        return "drop_out"
    else:
        return "<<error>>"

def print_tm(TM):
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
        if not isinstance(info[1], TargetScheme): 
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
            assert isinstance(target, TargetScheme)
            if target.scheme is not None: result.append(target)
        return result

    SL = get_target_scheme_list(TM)
    SL.sort(key=attrgetter("scheme"))

    print "BorderN    = %i" % (len(TM) - 1)
   
    tc_str = ""
    last_i = len(SL) - 1
    for i, info in enumerate(SL):
        tc_str += "%s" % scheme_str(info)
        if i != last_i: tc_str += ", "
    print "TargetComb = %s" % tc_str

