from   quex.input.regular_expression.construct         import Pattern
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.parallelize           as     parallelize
import quex.engine.state_machine.transformation        as     transformation
from   quex.engine.analyzer.commands                   import E_R, \
                                                              InputPDecrement, \
                                                              Assign
from   quex.engine.tools                               import all_isinstance, \
                                                              all_true, \
                                                              none_is_None, \
                                                              typed
from   quex.blackboard import setup as Setup, \
                              Lng
from   itertools       import ifilter

class EngineStateMachineSet:
    def __init__(self, PatternList): 
        assert isinstance(PatternList, list)
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


class CharacterSetStateMachine:
    def __init__(self, IncidenceIdMap):
        """Brief: Generates a state machine that implements the transition
        to terminals upon the input falling into a number set. 
            
                   .-----------------.
                   | character set 0 +---- - -> Incidence0
                   |                 |
                   | character set 1 +---- - -> Incidence1
                   |                 |
                   | character set 2 +---- - -> Incidence2
                   '-----------------'         

        The terminals related to the mentioned incidence ids are not implemented.
        If Setup.buffer_codec_transformation_info is defined the state machine
        is transformed accordingly.

        ARGUMENTS:

        IncidenceIdMap: List of tuples (NumberSet, IncidenceId) 

        """
        self.sm = self.__prepare(IncidenceIdMap)

        self.__prepare_begin_and_putback()
        self.__prepare_before_and_after_reload()

    def __prepare_begin_and_putback(self):
        """If we deal with variable character sizes, the begin of the letter is stored
        in 'character_begin_p'. To reset the input pointer 'input_p = character_begin_p' 
        is applied.
        """
        if not Setup.variable_character_sizes_f():
            # 1 character == 1 chunk
            # => rest to last character: 'input_p = input_p - 1'
            self.on_begin   = []
            self.on_putback = [ InputPDecrement() ]
        else:
            # 1 character == variable number of chunks
            # => store begin of character in 'lexeme_start_p'
            # => rest to last character: 'input_p = lexeme_start_p'
            self.on_begin   = [ Assign(E_R.CharacterBeginP, E_R.InputP) ]
            self.on_putback = [ Assign(E_R.InputP, E_R.CharacterBeginP) ]

    def __prepare_before_and_after_reload(self):
        """The 'lexeme_start_p' restricts the amount of data which is load into the
        buffer upon reload--if the lexeme needs to be maintained. If the lexeme
        does not need to be maintained, then the whole buffer can be refilled.
        
        For this, the 'lexeme_start_p' is set to the input pointer. 
        
        EXCEPTION: Variable character sizes. There, the 'lexeme_start_p' is used
        to mark the begin of the current letter. However, letters are short, so 
        the drawback is tiny.

        RETURN: [0] on_before_reload
                [1] on_after_reload
        """
        if not Setup.variable_character_sizes_f():
            self.on_before_reload = []
            self.on_after_reload  = []
        else:
            self.on_before_reload = [ Assign(E_R.LexemeStartP, E_R.InputP) ] 
            self.on_after_reload  = [ ] # Assign(E_R.InputP, E_R.LexemeStartP) ]

    def __prepare(self, IncidenceIdMap):
        sm = StateMachine()
        def add(sm, StateIndex, TriggerSet, IncidenceId):
            target_state_index = sm.add_transition(StateIndex, TriggerSet)
            target_state       = sm.states[target_state_index]
            target_state.mark_self_as_origin(IncidenceId, target_state_index)
            target_state.set_acceptance(True)

        sm         = StateMachine()
        init_state = sm.get_init_state()
        for character_set, incidence_id in IncidenceIdMap:
            # 'cliid' = unique command list incidence id.
            add(sm, sm.init_state_index, character_set, incidence_id)

        dummy, sm = transformation.do_state_machine(sm)
        return sm

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
              of dominated origins. This is important for pre-contexts, because,
              all successful patterns need to be reported!            
                      
    """   
    if len(StateMachine_List) == 0:
        return None

    def __check(Place, sm):
        __check_on_orphan_states(Place, sm)
        __check_on_init_state_not_acceptance(Place, sm)

    def __check_on_orphan_states(Place, sm):
        orphan_state_list = sm.get_orphaned_state_index_list()
        if len(orphan_state_list) == 0: return
        error_msg("After '%s'" % Place + "\n" + \
                  "Orphaned state(s) detected in regular expression (optimization lack).\n" + \
                  "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
                  "Orphan state(s) = " + repr(orphan_state_list)) 

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

