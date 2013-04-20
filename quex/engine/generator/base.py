from   quex.engine.misc.file_in                        import error_msg
from   quex.engine.generator.action_info               import PatternActionInfo
import quex.engine.generator.state_machine_coder       as     state_machine_coder
import quex.engine.generator.state_router              as     state_router_generator
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.languages.address         import address_set_subject_to_routing_add, \
                                                              get_address,                        \
                                                              get_label,                          \
                                                              get_label_of_address,               \
                                                              get_plain_strings,                  \
                                                              get_address_set_subject_to_routing, \
                                                              is_label_referenced
import quex.engine.state_machine.parallelize           as     parallelize
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
import quex.engine.state_machine.index                 as     index
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.transformation        as     transformation
import quex.engine.analyzer.transition_map             as     transition_map_tool
import quex.engine.analyzer.state.entry_action         as     entry_action
from   quex.engine.generator.state.transition.code     import TransitionCodeFactory
import quex.engine.generator.state.transition.core     as     transition_block
import quex.engine.analyzer.engine_supply_factory      as     engine
import quex.engine.analyzer.core                       as     analyzer_generator
from   quex.engine.interval_handling                   import NumberSet, Interval
from   quex.input.regular_expression.construct         import Pattern

from   quex.blackboard import E_ActionIDs, \
                              E_StateIndices, \
                              E_MapImplementationType, \
                              setup as Setup

from   itertools import ifilter
import re
from   copy import copy, deepcopy
from   collections import defaultdict

Match_input    = re.compile("\\binput\\b", re.UNICODE)
Match_iterator = re.compile("\\iterator\\b", re.UNICODE)

class GeneratorBase:
    def __init__(self, PatternActionPair_List):
        assert type(PatternActionPair_List) == list
        for x in PatternActionPair_List:
            assert    isinstance(x, PatternActionInfo) \
                   or x.pattern() in E_ActionIDs, repr(x)

        # self.state_machine_name = StateMachineName

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
        #    -- state machines that are non-trivially pre-contexted, 
        #       i.e. they need a reverse state machine to be verified.
        self.pre_context_sm_id_list  = []
        self.pre_context_sm_list     = []
        self.bipd_sm_list            = []
        # [NOT IMPLEMENTED YET]    
        # # trivial_pre_context_dict = {}             
        # map: state machine id --> character code(s)
        for pap in PatternActionPair_List:
            pattern = pap.pattern()
            if pattern in E_ActionIDs: 
                action_id = pattern
                # -- Register action of 'special action' such as 'ON_END_OF_STREAM', 'ON_FAILURE'
                self.action_db[action_id] = pap
                continue

            sm    = pattern.sm
            sm_id = sm.get_id()

            # -- register action information under the state machine id, where it belongs.
            self.action_db[sm_id] = pap

            # -- collect all 'core' state machines
            self.state_machine_list.append(sm)

            # -- collect all pre-contexts and make one single state machine out of it
            sm = pattern.pre_context_sm
            if sm is not None:
                self.pre_context_sm_list.append(sm)
                self.pre_context_sm_id_list.append(sm.get_id())
                
            # -- collect all backward input position detector state machines
            sm = pattern.bipd_sm
            if sm is not None:
                self.bipd_sm_list.append(sm)
                
            # -- collect all ids of post conditioned state machines
            if pattern.has_post_context():
                self.post_contexted_sm_id_list.append(sm_id)

            # [NOT IMPLEMENTED YET]    
            # # -- collect information about trivial (char code) pre-contexts 
            # # if len(sm.get_trivial_pre_context_character_codes()) != 0:
            # #    trivial_pre_context_dict[sm.get_id()] = sm.get_trivial_pre_context_character_codes()

        return

class Generator(GeneratorBase):

    def __init__(self, PatternActionPair_List):
        GeneratorBase.__init__(self, PatternActionPair_List)

    def code_pre_context_state_machine(self):
        LanguageDB = Setup.language_db

        if len(self.pre_context_sm_list) == 0: return []

        txt, dummy = Generator.code_state_machine(self.pre_context_sm, 
                                                  engine.BACKWARD_PRE_CONTEXT) 

        txt.append("\n%s" % LanguageDB.LABEL(E_StateIndices.END_OF_PRE_CONTEXT_CHECK))
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyzer went backwards, so it needs to be reset.
        txt.append("    %s\n" % LanguageDB.INPUT_P_TO_LEXEME_START())

        return txt

    def code_main_state_machine(self):
        LanguageDB    = Setup.language_db 

        sm_txt,       \
        terminal_txt, \
        analyzer      = self.code_state_machine_core(engine.FORWARD, False)

        # Number of different entries in the position register map
        self.__position_register_n                 = len(set(analyzer.position_register_map.itervalues()))
        self.__last_acceptance_variable_required_f = analyzer.last_acceptance_variable_required()

        return sm_txt + terminal_txt + LanguageDB.RELOAD()

    def code_state_machine_core(self, EngineType, SimpleF):
        sm_txt, analyzer = Generator.code_state_machine(self.sm, 
                                                        EngineType)
        terminal_txt     = Generator.code_terminals(self.action_db, 
                                                    self.pre_context_sm_id_list, 
                                                    SimpleF)
        return sm_txt, terminal_txt, analyzer


    def code_backward_input_position_detection(self):
        result = []
        for sm in self.bipd_sm_list:
            txt, dummy = Generator.code_state_machine(sm, engine.BACKWARD_INPUT_POSITION) 
            result.extend(txt)
        return result

    def state_router(self):
        # (*) Determine required labels and variables
        routed_address_set = get_address_set_subject_to_routing()
        routed_address_set.add(get_address("$terminal-EOF", U=True))
        routed_state_info_list = state_router_generator.get_info(routed_address_set)
        return [ state_router_generator.do(routed_state_info_list) ]

    def variable_definitions(self):
        # Variable to store the current input
        variable_db.require("input") 

        # Pre-Context Flags 
        for sm_id in self.pre_context_sm_id_list:
            variable_db.require("pre_context_%i_fulfilled_f", Index = sm_id)

        # Position registers
        if self.__position_register_n == 0:
            variable_db.require("position",          Initial = "(void*)0x0", Type = "void*")
            variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % self.__position_register_n)
        else:
            variable_db.require_array("position", ElementN = self.__position_register_n,
                                      Initial  = "{ " + ("0, " * (self.__position_register_n - 1) + "0") + "}")
            variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % self.__position_register_n)
    
        # Storage of 'last acceptance'
        if self.__last_acceptance_variable_required_f:
            variable_db.require("last_acceptance")

        # Target state index
        variable_db.require("target_state_index", Condition_ComputedGoto=False) 

        # Variables that tell where to go after reload success and reload failure
        if is_label_referenced("$reload-FORWARD") or is_label_referenced("$reload-BACKWARD"):
            variable_db.require("target_state_else_index")  # upon reload failure
            variable_db.require("target_state_index")       # upon reload success

        # Following function refers to the global 'variable_db'
        return Setup.language_db.VARIABLE_DEFINITIONS(variable_db)

    @staticmethod
    def code_function(ActionDB, FunctionPrefix, FunctionBody, VariableDefs, ModeNameList):
        analyzer_function = Setup.language_db["$analyzer-func"](FunctionPrefix,
                                                                Setup,
                                                                VariableDefs, 
                                                                FunctionBody, 
                                                                ModeNameList) 

        txt  = [ 
            Setup.language_db["$header-definitions"](Setup.language_db, 
                                                     ActionDB.get(E_ActionIDs.ON_AFTER_MATCH)) 
        ]
        txt.extend(get_plain_strings(analyzer_function))

        Generator.assert_txt(txt)

        return txt

    @staticmethod
    def code_state_machine(sm, EngineType, BeforeReloadAction=None): 
        assert len(sm.get_orphaned_state_index_list()) == 0

        LanguageDB = Setup.language_db

        txt = []
        # -- [optional] comment state machine transitions 
        if Setup.comment_state_machine_f:
            LanguageDB.ML_COMMENT(txt, 
                                  "BEGIN: STATE MACHINE\n"             + \
                                  sm.get_string(NormalizeF=False) + \
                                  "END: STATE MACHINE") 
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        # -- implement the state machine itself
        analyzer           = analyzer_generator.do(sm, EngineType)
        state_machine_code = state_machine_coder.do(analyzer, BeforeReloadAction)
        LanguageDB.REPLACE_INDENT(state_machine_code)

        txt.extend(state_machine_code)

        return txt, analyzer

    @staticmethod
    def code_terminals(ActionDB, PreContextID_List=None, SimpleF=False):
        """Implement the 'terminal', i.e. the actions which are performed
        once pattern have matched.
        """
        LanguageDB = Setup.language_db
        return LanguageDB["$terminal-code"](ActionDB, PreContextID_List, Setup, SimpleF) 

    @staticmethod
    def code_action_map(TM, IteratorName, 
                        BeforeReloadAction = None, 
                        AfterReloadAction  = None,
                        OnFailureAction    = None, 
                        ImplementationType = None):
        """TM is an object in the form of a 'transition map'. That is, it maps
        from an interval to an action--in this case not necessarily a state 
        transition. It consists of a list of pairs:

                               (interval, action)

        where the list is sorted by the interval's begin. Intervals shall not 
        interleave.
        """
        global Match_input
        global Match_iterator
        LanguageDB = Setup.language_db
        #OnFailureAction = None

        if ImplementationType is None: 
            reload_f           = (BeforeReloadAction is not None)
            ImplementationType = Generator.determine_implementation_type(TM, reload_f)

        # (*) Implement according to implementation type.
        if ImplementationType == E_MapImplementationType.TRIVIALIZED_STATE_MACHINE:
            # In case of variable character sizes, there can be no 'column_n +=
            # (iterator - reference_p) * C'. Thus, there is no 'AfterReloadAction'.
            # NOTE: code_action_state_machine_trivial() --> code_action_map_plain()
            txt = Generator.code_action_state_machine_trivial(TM, BeforeReloadAction, AfterReloadAction)

        elif ImplementationType == E_MapImplementationType.PLAIN_MAP:
            complete_f, tm = transformation.do_transition_map(TM)
            txt            = Generator.code_action_map_plain(tm, BeforeReloadAction, AfterReloadAction)

        elif ImplementationType == E_MapImplementationType.STATE_MACHINE:
            txt = Generator.code_action_state_machine(TM, BeforeReloadAction, AfterReloadAction,
                                                      OnFailureAction)

        else:
            assert False

        return ImplementationType, \
               Generator.replace_iterator_name(txt, IteratorName, ImplementationType)

    @staticmethod
    def determine_implementation_type(TM, ReloadF):
        if Setup.variable_character_sizes_f():
            if     not ReloadF \
               and Generator.state_machine_trivial_possible(TM):
                return E_MapImplementationType.TRIVIALIZED_STATE_MACHINE
            else:
                return E_MapImplementationType.STATE_MACHINE
        else:
            return E_MapImplementationType.PLAIN_MAP

    @staticmethod
    def code_action_state_machine(TM, BeforeReloadAction, AfterReloadAction, OnFailureAction):
        """Generates a state machine that represents the transition map 
        according to the codec given in 'Setup.buffer_codec_transformation_info'
        """
        LanguageDB = Setup.language_db
        assert TM is not None

        # Here, characters are made up of more than one 'chunk'. When the last
        # character needs to be reset, its start position must be known. For 
        # this the 'lexeme start pointer' is used.
        if      BeforeReloadAction is not None \
            and transition_map_tool.has_action_id(TM, E_ActionIDs.ON_EXIT):
            variable_db.require("character_begin_p")

            loop_epilog = [1, "%s\n" % LanguageDB.CHARACTER_BEGIN_P_SET()]
            transition_map_tool.replace_action_id(TM, E_ActionIDs.ON_EXIT, 
                                                  [1, "%s\n" % LanguageDB.INPUT_P_TO_CHARACTER_BEGIN_P()])
            BeforeReloadAction.append("%s\n" % LanguageDB.LEXEME_START_TO_CHARACTER_BEGIN_P())
            AfterReloadAction.append("%s\n" % LanguageDB.CHARACTER_BEGIN_P_TO_LEXEME_START_P())
        else:
            loop_epilog = []

        # Now, we start with code generation. The signalizing ActionIDs must be deleted.
        transition_map_tool.delete_action_ids(TM)

        pap_list = get_pattern_action_pair_list_from_map(TM)
        for pap in pap_list:
            pap.pattern().transform(Setup.buffer_codec_transformation_info)

        if OnFailureAction is not None:
            pap_list.append(PatternActionInfo(E_ActionIDs.ON_FAILURE, 
                                              OnFailureAction))

        generator = Generator(pap_list) 

        if BeforeReloadAction is None: 
            engine_type = engine.CHARACTER_COUNTER
        else:                          
            engine_type = engine.FORWARD
            generator.sm.delete_transitions_on_interval(Interval(Setup.buffer_limit_code))
            generator.sm.delete_orphaned_states()

        if BeforeReloadAction is not None:
            reload_label = Generator.generate_reload_label()
            LanguageDB.code_generation_reload_label_set(reload_label)

        sm_txt,       \
        terminal_txt, \
        dummy         = generator.code_state_machine_core(engine_type, SimpleF=True)

        reload_txt = []
        if BeforeReloadAction is not None:
            reload_txt = LanguageDB.RELOAD_SPECIAL(BeforeReloadAction, AfterReloadAction)
            LanguageDB.code_generation_reload_label_set(None)

        return loop_epilog + sm_txt + terminal_txt + reload_txt

    @staticmethod
    def state_machine_trivial_possible(tm):
        """Checks whether the 'trivial' implementation of the state machine 
        for UTF8 or UTF16 is possible. 

        IDEA: If all characters > LowestRangeBorder cause the same action.
              then a trivial map can be implemented:

              if( *iterator > LowestRangeBorder ) {
                  Action
                  Increment iterator according to incoming bytes
              }
              Transition map based on a single chunk '*iterator'.
        """
        if   Setup.buffer_codec_transformation_info == "utf8-state-split":
            LowestRangeBorder = 0x80 
        elif Setup.buffer_codec_transformation_info == "utf16-state-split":
            LowestRangeBorder = 0x10000 
        else:
            return False


        if tm[-1][0].begin >= LowestRangeBorder: 
            return False

        return True

    @staticmethod
    def code_action_state_machine_trivial(tm, BeforeReloadAction, AfterReloadAction):
        """This function tries to provide easy solutions for dynamic character
        length encodings, such as UTF8 or UTF16. 
        
        The simplification:

        Check whether all critical checks from inside the 'counter_db' happen in
        the range where there is only one chunk considered (UTF8->1byte at x <
        0x800, UTF16->2byte at x < 0x10000). The range is identified by
        'LowestRangeBorder'. Then implement a simple transition map for this range.
        The remainder of the counter function only implements the input pointer
        increments. They come from a template string given by
        'IncrementActionStr'.

        NOTE: Currently, this is only implemented for 'counter'. Nothing where
        reload is involved may use this function.

        RETURNS: None -- if no easy solution could be provided.
                 text -- the implementation of the counter functionh.
        """
        global _increment_actions_for_utf16
        global _increment_actions_for_utf8
        LanguageDB = Setup.language_db
       
        # Currently, we do not handle the case 'Reload': refuse to work.
        assert BeforeReloadAction is None
        assert Generator.state_machine_trivial_possible(tm)
        transition_map_tool.assert_continuity(tm) #, str([x[0] for x in tm])

        # (*) Try to find easy and elegant special solutions 
        if   Setup.buffer_codec_transformation_info == "utf8-state-split":
            IncrementActionStr = _increment_actions_for_utf8
        elif Setup.buffer_codec_transformation_info == "utf16-state-split":
            IncrementActionStr = _increment_actions_for_utf16
        else:
            assert False

        # (*) Add increment actions to the actions
        def add_increment(action, IncrementActionStr, LastF):
            if LastF:
                action = deepcopy(action) # disconnect from same action on other interval
                assert E_ActionIDs.ON_GOOD_TRANSITION in action
                idx = action.index(E_ActionIDs.ON_GOOD_TRANSITION)
                # Delete 'ON_GOOD_TRANSITION' prevents 
                # 'code_action_map_plain()' from adding '++iterator'.
                del action[idx]
                for x in reversed(IncrementActionStr):
                    action.insert(idx, x)
            return action

        LastI = len(tm) - 1
        tm = [ (x[0], add_increment(x[1], IncrementActionStr, LastF=(i==LastI))) 
               for i, x in enumerate(tm) ]

        # (*) The first interval may start at - sys.maxint
        if tm[0][0].begin < 0: tm[0][0].begin = 0

        # Later interval shall not be less than 0!
        assert tm[0][0].end > 0

        # Code the transition map
        return Generator.code_action_map_plain(tm) # No reload possible (see entry assert) 

    @staticmethod
    def code_action_map_plain(TM, BeforeReloadAction=None, AfterReloadAction=None):

        LanguageDB = Setup.language_db

        if BeforeReloadAction is None: 
            engine_type = engine.CHARACTER_COUNTER
        else:                          
            engine_type = engine.FORWARD
            AfterReloadAction.insert(0, "%s\n" % LanguageDB.INPUT_P_INCREMENT())
            AfterReloadAction.insert(0, 1)

            transition_map_tool.set_target(TM, Setup.buffer_limit_code,
                                           E_StateIndices.DROP_OUT)
            BeforeReloadAction.append("%s\n" % LanguageDB.LEXEME_START_SET())

            #transition_map_tool.replace_action_id(TM, E_ActionIDs.ON_EXIT, 
            #                                      [1, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])

        transition_map_tool.insert_after_action_id(TM, E_ActionIDs.ON_GOOD_TRANSITION,
                                                   [2, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])
        # The range of possible characters may be restricted. It must be ensured,
        # that the occurring characters only belong to the admissible range.
        transition_map_tool.prune(TM, 0, Setup.get_character_value_limit())

        # Now, we start with code generation. The signalizing ActionIDs must be deleted.
        transition_map_tool.delete_action_ids(TM)

        txt = []
        pseudo_state_index = LanguageDB.ADDRESS(index.get(), None)
        if BeforeReloadAction is not None:
            upon_reload_done_label = "%s:\n" % LanguageDB.ADDRESS_LABEL(pseudo_state_index)
            reload_label           = Generator.generate_reload_label()
            LanguageDB.code_generation_reload_label_set(reload_label)
            LanguageDB.code_generation_on_reload_fail_adr_set(get_address("$terminal-EOF", U=True))

            assert engine_type.requires_buffer_limit_code_for_reload()

            txt = [ upon_reload_done_label ]

        TransitionCodeFactory.init(engine_type, StateIndex = pseudo_state_index)

        if BeforeReloadAction is not None:
            TransitionCodeFactory.prepare_reload_tansition(TM, pseudo_state_index)

        tm = [ 
            (interval, TransitionCodeFactory.do(x)) for interval, x in TM 
        ]

        #LanguageDB.code_generation_switch_cases_add_statement("break;")
        transition_block.do(txt, tm)
        #LanguageDB.code_generation_switch_cases_add_statement(None)

        reload_txt = []
        if BeforeReloadAction is not None:
            assert engine_type.requires_buffer_limit_code_for_reload()
            reload_txt = LanguageDB.RELOAD_SPECIAL(BeforeReloadAction, AfterReloadAction)
            LanguageDB.code_generation_reload_label_set(None)
            LanguageDB.code_generation_on_reload_fail_adr_set(None)

        return txt + reload_txt

    @staticmethod
    def generate_reload_label():
        LanguageDB = Setup.language_db
        reload_adr   = LanguageDB.ADDRESS(index.get(), None)
        return get_label_of_address(reload_adr, U=False) # Not subject to routing

    @staticmethod
    def replace_iterator_name(txt, IteratorName, ImplementationType):
        assert ImplementationType in E_MapImplementationType
        StateMachineF = (ImplementationType == E_MapImplementationType.STATE_MACHINE)
        def replacer(block, StateMachineF):
            if block.find("me->buffer._input_p") != -1: 
                block = block.replace("me->buffer._input_p", "(%s)" % IteratorName)
            if not StateMachineF:
                block = Match_input.sub("(*%s)" % IteratorName, block)
                block = Match_iterator.sub("(%s)" % IteratorName, block)
            return block

        for i, elm in enumerate(txt):
            if not isinstance(elm, (str, unicode)): continue
            txt[i] = replacer(elm, StateMachineF)

        return txt

    @staticmethod
    def delete_action_ids(txt):
        i = L - 1
        while i >= 0:
            if txt[i] in E_ActionIDs:
                del txt[i]
            i -= 1
        return

    @staticmethod
    def assert_txt(txt):
        for i, element in enumerate(txt):
            if isinstance(element, (str, unicode)): continue
            print element.__class__.__name__
            for k in range(max(0,i-10)):
                print "before:", k, txt[k]
            for k in range(i+1, min(i+10, len(txt))):
                print "after: ", k, txt[k]
            assert False

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

def get_pattern_action_pair_list_from_map(TM):
    """Returns a state machine list which implements the transition map given
    in unicode. It is assumed that the codec is a variable
    character size codec. Each count action is associated with a separate
    state machine in the list. The association is recorded in 'action_db'.

    RETURNS: [0] -- The 'action_db': state_machine_id --> count action
             [1] -- The list of state machines. 
    """
    # Sort by actions.
    action_code_db = defaultdict(NumberSet)
    for character_set, action_list in TM:
        if action_list == E_StateIndices.DROP_OUT: continue
        assert isinstance(action_list, list)
        # Make 'action_list' a tuple so that it is hash-able
        action_code_db[tuple(action_list)].unite_with(character_set)

    pattern_action_pair_list = []
    for action, trigger_set in action_code_db.iteritems():
        # Make 'action' a list again, so that it can be used as CodeFragment
        action = list(action)
        pattern = Pattern(StateMachine.from_character_set(trigger_set))
        pattern_action_pair_list.append(PatternActionInfo(pattern, action))

    return pattern_action_pair_list

_increment_actions_for_utf8 = [
     1, "if     ( ((*iterator) & 0x80) == 0 ) { iterator += 1; } /* 1byte character */\n",
     1, "/* NOT ( ((*iterator) & 0x40) == 0 ) { iterator += 2; }    2byte character */\n",
     1, "else if( ((*iterator) & 0x20) == 0 ) { iterator += 2; } /* 2byte character */\n",
     1, "else if( ((*iterator) & 0x10) == 0 ) { iterator += 3; } /* 3byte character */\n",
     1, "else if( ((*iterator) & 0x08) == 0 ) { iterator += 4; } /* 4byte character */\n",
     1, "else if( ((*iterator) & 0x04) == 0 ) { iterator += 5; } /* 5byte character */\n",
     1, "else if( ((*iterator) & 0x02) == 0 ) { iterator += 6; } /* 6byte character */\n",
     1, "else if( ((*iterator) & 0x01) == 0 ) { iterator += 7; } /* 7byte character */\n",
     1, "else                                 { iterator += 1; } /* default 1       */\n",
]
    
_increment_actions_for_utf16 = [
     1, "if( *iterator >= 0xD800 && *iterator < 0xE000 ) { iterator += 2; }\n",
     1, "else                                            { iterator += 1; }\n", 
]
    
