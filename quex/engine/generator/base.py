from   quex.engine.misc.file_in                        import error_msg
from   quex.engine.generator.action_info               import PatternActionInfo
import quex.engine.state_machine.parallelize           as parallelize
import quex.engine.state_machine.algorithm.beautifier  as beautifier
import quex.engine.state_machine.transformation     as transformation

from   quex.blackboard import setup as Setup

from   itertools import ifilter

class GeneratorBase:
    def __init__(self, PatternActionPair_List, StateMachineName):
        assert type(PatternActionPair_List) == list
        assert map(lambda elm: elm.__class__ == PatternActionInfo, PatternActionPair_List) \
               == [ True ] * len(PatternActionPair_List)

        self.state_machine_name        = StateMachineName

        # -- setup of state machine lists and id lists
        self.__extract_special_lists(PatternActionPair_List)

        # (*) create state (combined) state machines
        #     -- core state machine
        self.sm                 = get_combined_state_machine(self.state_machine_list)

        #     -- pre conditions, combined into a single state machine
        if len(self.pre_context_sm_list) != 0:
            self.pre_context_sm = get_combined_state_machine(self.pre_context_sm_list, 
                                                             FilterDominatedOriginsF=False)
        else:
            self.pre_context_sm = None

    def __extract_special_lists(self, PatternActionPair_List):
        # (0) extract data structures:
        #      -- state machine list: simply a list of all state machines
        #         (the original state machine id is marked as 'origin' inside 
        #          'get_state_machine')
        #      -- a map from state machine id to related action (i.e. the code fragment) 
        self.state_machine_list = []
        self.action_db          = {}
        # -- extract:
        #    -- state machines that are post-conditioned
        self.post_contexted_sm_id_list = []
        #    -- state machines that are non-trivially pre-conditioned, 
        #       i.e. they need a reverse state machine to be verified.
        self.pre_context_sm_id_list  = []
        self.pre_context_sm_list     = []
        self.bipd_sm_list            = []
        # [NOT IMPLEMENTED YET]    
        # # trivial_pre_context_dict = {}             
        # map: state machine id --> character code(s)
        for pap in PatternActionPair_List:
            pattern = pap.pattern()
            sm      = pattern.sm
            sm_id   = sm.get_id()
            self.state_machine_list.append(sm)

            # -- register action information under the state machine id, where it belongs.
            self.action_db[sm_id] = pap

            # -- collect all pre-conditions and make one single state machine out of it
            sm = pattern.pre_context_sm
            if sm is not None:
                self.pre_context_sm_list.append(sm)
                self.pre_context_sm_id_list.append(sm.get_id())
                
            # -- collect all backward input position detector state machines
            sm = pattern.bipd_sm
            if sm is not None:
                self.bipd_sm_list.append(sm)
                
            # -- collect all ids of post conditioned state machines
            if pattern.post_context_f:
                self.post_contexted_sm_id_list.append(sm_id)

            # [NOT IMPLEMENTED YET]    
            # # -- collect information about trivial (char code) pre-conditions 
            # # if len(sm.get_trivial_pre_context_character_codes()) != 0:
            # #    trivial_pre_context_dict[sm.get_id()] = sm.get_trivial_pre_context_character_codes()

        return

def get_combined_state_machine(StateMachine_List, FilterDominatedOriginsF=True):
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
              of dominated origins. This is important for pre-conditions, because,
              all successful patterns need to be reported!            
                      
    """   
    def __check(Place, sm):
        __check_on_orphan_states(Place, sm)
        __check_on_init_state_not_acceptance(Place, sm)

    def __check_on_orphan_states(Place, sm):
        orphan_state_list = sm.get_orphaned_state_index_list()
        if len(orphan_state_list) == 0: return
        error_msg("After '%s'" % Place + "\n" + \
                  "Orphaned state(s) detected in regular expression (optimization lack).\n" + \
                  "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
                  "Orphan state(s) = " + repr(orphan_state_list)                       + "\n") 

    def __check_on_init_state_not_acceptance(Place, sm):
        init_state = sm.get_init_state()
        if init_state.is_acceptance():
            error_msg("After '%s'" % Place + "\n" + \
                      "The initial state is 'acceptance'. This should never appear.\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n")

        for dummy in ifilter(lambda origin: origin.is_acceptance(), init_state.origins()):
            error_msg("After '%s'" % Place + "\n" + \
                      "Initial state contains an origin that is 'acceptance'. This should never appear.\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n")

    # (1) mark at each state machine the machine and states as 'original'.
    #      
    #     This is necessary to trace in the combined state machine the
    #     pattern that actually matched. Note, that a state machine in
    #     the StateMachine_List represents one possible pattern that can
    #     match the current input.   
    #
    for sm in StateMachine_List:
        sm.mark_state_origins()
        assert sm.is_DFA_compliant(), sm.get_string(Option="hex")

    # (2) setup all patterns in paralell 
    sm = parallelize.do(StateMachine_List, CommonTerminalStateF=False) #, CloneF=False)
    __check("Parallelization", sm)

    # (4) determine for each state in the DFA what is the dominating original state
    if FilterDominatedOriginsF: sm.filter_dominated_origins()
    __check("Filter Dominated Origins", sm)

    # (3) convert the state machine to an DFA (paralellization created an NFA)
    sm = beautifier.do(sm)
    __check("NFA to DFA, Hopcroft Minimization", sm)
    
    return sm
