from   quex.input.regular_expression.construct         import Pattern
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.construction.parallelize as     parallelize
from   quex.engine.analyzer.door_id_address_label      import dial_db
from   quex.engine.operations.operation_list           import Op
import quex.engine.misc.error                          as     error
from   quex.engine.misc.tools                          import all_isinstance, \
                                                              all_true, \
                                                              concatinate, \
                                                              typed

from   quex.blackboard import setup as Setup, \
                              E_R

class EngineStateMachineSet:
    def __init__(self, PatternList): 
        assert isinstance(PatternList, list)
        assert len(PatternList) > 0
        assert all_isinstance(PatternList, Pattern)
        assert all_true(PatternList, lambda p: p.incidence_id() is not None)

        # (*) Core SM, Pre-Context SM, ...
        #     ... and sometimes backward input position SMs.
        self.sm,                    \
        self.pre_context_sm,        \
        self.bipd_sm_db,            \
        self.pre_context_sm_id_list = self.__prepare(PatternList)

    def __prepare(self, PatternList):
        # -- setup of state machine lists and id lists
        core_sm_list,                 \
        pre_context_sm_list,          \
        incidence_id_and_bipd_sm_list = self.__prepare_sm_lists(PatternList)

        # (*) Create (combined) state machines
        #     Backward input position detection (bipd) remains separate engines.
        return get_combined_state_machine(core_sm_list),                  \
               get_combined_state_machine(pre_context_sm_list,            \
                                          FilterDominatedOriginsF=False), \
               dict((incidence_id, sm) for incidence_id, sm in incidence_id_and_bipd_sm_list), \
               [ sm.get_id() for sm in pre_context_sm_list ]

    def __prepare_sm_lists(self, PatternList):
        # -- Core state machines of patterns
        state_machine_list = [ pattern.sm for pattern in PatternList ]

        # -- Pre-Contexts
        pre_context_sm_list = [    
            pattern.pre_context_sm for pattern in PatternList \
            if pattern.pre_context_sm is not None 
        ]

        # -- Backward input position detection (BIPD)
        bipd_sm_list = [
            (pattern.incidence_id(), pattern.bipd_sm) for pattern in PatternList \
            if pattern.bipd_sm is not None 
        ]
        return state_machine_list, pre_context_sm_list, bipd_sm_list

def get_combined_state_machine(StateMachine_List, FilterDominatedOriginsF=True,
                               MarkNotSet=set(), AlllowInitStateAcceptF=False):
    """Creates a DFA state machine that incorporates the paralell
       process of all pattern passed as state machines in 
       the StateMachine_List. Each origins of each state machine
       are kept in the final state, if it is not dominated.

       Performs: -- parallelization
                 -- translation from NFA to DFA
                 -- Frank Schaefers Adapted Hopcroft optimization.

       Again: The state machine ids of the original state machines
              are traced through the whole process.
              
       FilterDominatedOriginsF, if set to False, can disable the filtering
              of dominated origins. This is important for pre-contexts, because,
              all successful patterns need to be reported!            
                      
    """   
    if len(StateMachine_List) == 0:
        return None

    def __check(Place, sm, AlllowInitStateAcceptF):
        __check_on_orphan_states(Place, sm)
        if not AlllowInitStateAcceptF:
            __check_on_init_state_not_acceptance(Place, sm)

    def __check_on_orphan_states(Place, sm):
        orphan_state_list = sm.get_orphaned_state_index_list()
        if len(orphan_state_list) == 0: return
        error.log("After '%s'" % Place + "\n" + \
                  "Orphaned state(s) detected in regular expression (optimization lack).\n" + \
                  "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
                  "Orphan state(s) = " + repr(orphan_state_list)) 

    def __check_on_init_state_not_acceptance(Place, sm):
        if sm.get_init_state().is_acceptance():
            error.log("After '%s'" % Place + "\n" + \
                      "Initial state 'accepts'. This should never happen.\n" + \
                      "Please, log a defect at the projects web site quex.sourceforge.net.\n")

    # (1) mark at each state machine the machine and states as 'original'.
    #      
    # This is necessary to trace in the combined state machine the pattern that
    # actually matched. Note, that a state machine in the StateMachine_List
    # represents one possible pattern that can match the current input.   
    #
    for sm in StateMachine_List:
        if sm.get_id() in MarkNotSet: continue
        sm.mark_state_origins()
        assert sm.is_DFA_compliant(), sm.get_string(Option="hex")

    # (2) setup all patterns in paralell 
    sm = parallelize.do(StateMachine_List, CommonTerminalStateF=False) #, CloneF=False)
    __check("Parallelization", sm, AlllowInitStateAcceptF)

    # (4) determine for each state in the DFA what is the dominating original 
    #     state
    if FilterDominatedOriginsF: sm.filter_dominated_origins()
    __check("Filter Dominated Origins", sm, AlllowInitStateAcceptF)

    # (3) convert the state machine to an DFA (paralellization created an NFA)
    sm = beautifier.do(sm)
    __check("NFA to DFA, Hopcroft Minimization", sm, AlllowInitStateAcceptF)
    
    return sm



        

