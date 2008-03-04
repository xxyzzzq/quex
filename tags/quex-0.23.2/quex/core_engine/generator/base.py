import quex.core_engine.state_machine.parallelize as     parallelize
from   quex.core_engine.generator.action_info     import ActionInfo
from   quex.core_engine.state_machine.index       import get_state_machine_by_id

class GeneratorBase:
    def __init__(self, PatternActionPair_List, StateMachineName, ControlCharacterCodeList):
        assert type(PatternActionPair_List) == list
        assert map(lambda elm: elm.__class__ == ActionInfo, PatternActionPair_List) \
               == [ True ] * len(PatternActionPair_List)

        self.state_machine_name = StateMachineName

        # -- setup of state machine lists and id lists
        self.__extract_special_lists(PatternActionPair_List)

        # (*) create state (combined) state machines
        #     -- core state machine
        self.sm = self.__create_core_state_machine()
        #     -- pre conditions
        self.pre_condition_sm = self.__create_pre_context_state_machine()
        #     -- backward detectors for state machines with forward ambiguous
        #        post-conditions.
        self.papc_backward_detector_state_machine_list = \
                self.__create_backward_input_position_detectors()

        # (*) extract any control character in the transitions that could
        #     block the buffer handling (end of buffer/end of file)
        self.__extract_control_characters_from_transitions(self.sm, ControlCharacterCodeList)
        if self.pre_condition_sm != None:
            self.__extract_control_characters_from_transitions(self.pre_condition_sm, ControlCharacterCodeList)
        if self.papc_backward_detector_state_machine_list != []:
            for sm in self.papc_backward_detector_state_machine_list:
                self.__extract_control_characters_from_transitions(sm, ControlCharacterCodeList)

    def __extract_control_characters_from_transitions(self, sm, ControlCharacterCodeList):
        for state in sm.states.values():
            state.delete_transitions_on_character_list(ControlCharacterCodeList)

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
        self.post_conditioned_sm_id_list = []
        #    -- state machines that nore non-trivially pre-conditioned, 
        #       i.e. they need a reverse state machine to be verified.
        self.pre_condition_sm_id_list  = []
        self.pre_condition_sm_list     = []
        #    -- pre-conditions that are trivial, i.e. it is only checked for
        #       the last character, if it was a particular one or not.
        self.begin_of_line_condition_f = False
        # [NOT IMPLEMENTED YET]    
        # # trivial_pre_condition_dict = {}             # map: state machine id --> character code(s)
        for action_info in PatternActionPair_List:
            sm = action_info.pattern_state_machine()
            self.state_machine_list.append(sm)
            # -- register action information under the state machine id, where it 
            #    belongs.
            origins_of_acceptance_states = sm.get_origin_ids_of_acceptance_states()
            assert len(origins_of_acceptance_states) != 0, \
                   "error: code generation for pattern:\n" + \
                   "error: no acceptance state contains origin information.\n" + \
                   repr(sm)
            origin_state_machine_id = origins_of_acceptance_states[0]
            self.action_db[origin_state_machine_id] = action_info

            # -- collect all pre-conditions and make one single state machine out of it
            if sm.has_non_trivial_pre_condition():
                pre_sm = sm.pre_condition_state_machine
                self.pre_condition_sm_list.append(pre_sm)
                self.pre_condition_sm_id_list.append(pre_sm.get_id())
                
            if sm.has_trivial_pre_condition_begin_of_line():
                self.begin_of_line_condition_f = True

            # [NOT IMPLEMENTED YET]    
            # # -- collect information about trivial (char code) pre-conditions 
            # # if sm.get_trivial_pre_condition_character_codes() != []:
            # #    trivial_pre_condition_dict[sm.get_id()] = sm.get_trivial_pre_condition_character_codes()

            # -- collect all ids of post conditioned state machines
            if sm.is_post_conditioned():
                self.post_conditioned_sm_id_list.append(origin_state_machine_id)

    def __create_core_state_machine(self):
        # (1) transform all given patterns into a single state machine
        #     (the index of the patterns remain as 'origins' inside the states)
        return self.__get_combined_state_machine(self.state_machine_list)

    def __create_pre_context_state_machine(self):
        if self.pre_condition_sm_list == []: return None

        # -- add empty actions for the pre-condition terminal states
        for pre_sm in self.pre_condition_sm_list:
            self.action_db[pre_sm.get_id()] = ActionInfo(pre_sm, "")

        return self.__get_combined_state_machine(self.pre_condition_sm_list, 
                                                 FilterDominatedOriginsF=False)

    def __create_backward_input_position_detectors(self):
        # -- find state machines that contain a state flagged with 
        #    'pseudo-ambiguous-post-condition'.
        papc_sm_id_list = filter(lambda backward_detector_id: backward_detector_id != -1L,
                                 map(lambda sm: sm.get_pseudo_ambiguous_post_condition_id(),
                                     self.state_machine_list))

        # -- collect all mentioned state machines in a list
        return map(get_state_machine_by_id, papc_sm_id_list)

    def __get_combined_state_machine(self, StateMachine_List, FilterDominatedOriginsF=True):
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
        # (1) mark at each state machine the machine and states as 'original'.
        #      
        #     This is necessary to trace in the combined state machine the
        #     pattern that actually matched. Note, that a state machine in
        #     the StateMachine_List represents one possible pattern that can
        #     match the current input.   
        #
        map(lambda x: x.mark_state_origins(DontMarkIfOriginsPresentF=True), StateMachine_List)
        
        # (2) setup all patterns in paralell 
        sm = parallelize.do(StateMachine_List)

        # (3) convert the state machine to an DFA (paralellization created an NFA)
        sm = sm.get_DFA()

        # (4) determine for each state in the DFA what is the dominating original state
        if FilterDominatedOriginsF: sm.filter_dominated_origins()

        # (5) perform hopcroft optimization
        #     Note, that hopcroft optimization does consider the original acceptance 
        #     states when deciding if two state sets are equivalent.   
        sm = sm.get_hopcroft_optimization()    

        return sm
