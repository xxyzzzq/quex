from   quex.engine.misc.file_in                        import error_msg
from   quex.engine.generator.action_info               import PatternActionInfo
import quex.engine.generator.state_machine_coder       as     state_machine_coder
import quex.engine.generator.state_router              as     state_router_generator
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.languages.address         import address_set_subject_to_routing_add, \
                                                              get_address,                        \
                                                              get_plain_strings,                  \
                                                              get_address_set_subject_to_routing, \
                                                              is_label_referenced
import quex.engine.state_machine.parallelize           as     parallelize
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
import quex.engine.state_machine.index                 as     index
import quex.engine.state_machine.transformation        as     transformation
import quex.engine.analyzer.transition_map             as     transition_map_tool
from   quex.engine.generator.state.transition.code     import TransitionCodeFactory
import quex.engine.generator.state.transition.core     as     transition_block
import quex.engine.analyzer.engine_supply_factory      as     engine
import quex.engine.analyzer.core                       as     analyzer_generator
from   quex.input.regular_expression.construct         import Pattern

from   quex.blackboard import E_ActionIDs, \
                              E_StateIndices, \
                              setup as Setup

from   itertools import ifilter
import re
from   copy import copy

Match_input    = re.compile("\\binput\\b", re.UNICODE)
Match_iterator = re.compile("\\iterator\\b", re.UNICODE)

class GeneratorBase:
    def __init__(self, PatternActionPair_List):
        assert type(PatternActionPair_List) == list
        assert map(lambda elm: elm.__class__ == PatternActionInfo, PatternActionPair_List) \
               == [ True ] * len(PatternActionPair_List)

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

    def code_main_state_machine(self, EngineType=engine.FORWARD, BeforeGotoReloadAction=None):
        LanguageDB       = Setup.language_db 

        sm_txt, analyzer = Generator.code_state_machine(self.sm, EngineType, BeforeGotoReloadAction)
        terminal_txt     = Generator.code_terminals(self.action_db, self.pre_context_sm_id_list)

        # -- reload definition (forward, backward, init state reload)
        if EngineType.requires_buffer_limit_code_for_reload():
            reload_txt = LanguageDB.RELOAD()
        else:
            reload_txt = ""

        # Number of different entries in the position register map
        self.__position_register_n                 = len(set(analyzer.position_register_map.itervalues()))
        self.__last_acceptance_variable_required_f = analyzer.last_acceptance_variable_required()

        return sm_txt + terminal_txt + reload_txt

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
                                                     ActionDB[E_ActionIDs.ON_AFTER_MATCH]) 
        ]
        txt.extend(get_plain_strings(analyzer_function))

        Generator.assert_txt(txt)

        return txt

    @staticmethod
    def code_state_machine(sm, EngineType, BeforeGotoReloadAction=None): 
        assert len(sm.get_orphaned_state_index_list()) == 0

        LanguageDB = Setup.language_db

        txt = []
        # -- [optional] comment state machine transitions 
        if Setup.comment_state_machine_f:
            LanguageDB.ML_COMMENT(txt, 
                                  "BEGIN: STATE MACHINE\n"             + \
                                  self.sm.get_string(NormalizeF=False) + \
                                  "END: STATE MACHINE") 
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        # -- implement the state machine itself
        analyzer           = analyzer_generator.do(sm, EngineType)
        state_machine_code = state_machine_coder.do(analyzer, BeforeGotoReloadAction)
        LanguageDB.REPLACE_INDENT(state_machine_code)

        txt.extend(state_machine_code)

        return txt, analyzer

    @staticmethod
    def code_terminals(ActionDB, PreContextID_List=None):
        """Implement the 'terminal', i.e. the actions which are performed
        once pattern have matched.
        """
        LanguageDB = Setup.language_db
        return LanguageDB["$terminal-code"](ActionDB, PreContextID_List, Setup) 

    @staticmethod
    def code_action_map(TM, IteratorName, 
                        BeforeGotoReloadAction = None, 
                        OnFailureAction        = None):
        """TM is an object in the form of a 'transition map'. That is, it maps
        from an interval to an action--in this case not necessarily a state 
        transition. It consists of a list of pairs:

                               (interval, action)

        where the list is sorted by the interval's begin. Intervals shall not 
        interleave.
        """
        global Match_input
        global Match_iterator

        StateMachineF = Setup.variable_character_sizes_f()

        if StateMachineF:
            upon_reload_done_adr = None

            txt = _trivialized_state_machine_coder_do(TM, BeforeGotoReloadAction)
            if txt is not None:
                StateMachineF = False # We tricked around it; No state machine needed.
            else:
                txt = Generator.code_action_state_machine(TM, BeforeGotoReloadAction, OnFailureAction)
        else:
            upon_reload_done_adr = index.get()
            address_set_subject_to_routing_add(upon_reload_done_adr) # Mark as 'used'

            complete_f, tm = transformation.do_transition_map(TM)
            txt            = _transition_map_coder_do(tm, BeforeGotoReloadAction, upon_reload_done_adr)

        return StateMachineF, \
               replace_iterator_name(txt, IteratorName, StateMachineF), \
               upon_reload_done_adr

    @staticmethod
    def code_action_state_machine(TM, BeforeGotoReloadAction, OnFailureAction):
        """Generates a state machine that represents the transition map 
        according to the codec given in 'Setup.buffer_codec_transformation_info'
        """
        assert sm is not None

        pap_list  = get_pattern_action_pair_list_from_map(tm, BeforeGotoReloadAction is not None)
        for pap in pap_list:
            pap.transform(Setup.buffer_codec_transformation_info)

        if OnFailureAction is not None:
            pap_list.append(PatternActionInfo(E_ActionIDs.ON_FAILURE, 
                                              OnFailureAction))

        if BeforeGotoReloadAction is None: engine_type = engine.CHARACTER_COUNTER
        else:                              engine_type = engine.FORWARD

        generator = CppGenerator(pap_list) 

        # assert E_ActionIDs.ON_AFTER_MATCH not in action_db
        # assert E_ActionIDs.ON_FAILURE     not in action_db
        # complete_f, sm = transformation.do_state_machine(sm)

        return generator.code_main_state_machine(engine_type, BeforeGotoReloadAction)

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
        action_code_db[tuple(action_list)].unite_with(character_set)

    pattern_action_pair_list = []
    for action, trigger_set in action_code_db.iteritems():
        pattern = Pattern(StateMachine.from_character_set(trigger_set))
        pattern_action_pair_list.append(PatternActionInfo(pattern, action))

    return pattern_action_pair_list

def _trivialized_state_machine_coder_do(tm, BeforeGotoReloadAction):
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

    RETURNS: None -- if no easy solution could be provided.
             text -- the implementation of the counter functionh.
    """
    global __increment_actions_for_utf16
    global __increment_actions_for_utf8
   
    # Currently, we do not handle the case 'Reload': refuse to work.
    if BeforeGotoReloadAction is not None:
        return None

    # (*) Try to find easy and elegant special solutions 
    if   Setup.buffer_codec_transformation_info == "utf8-state-split":
        LowestRangeBorder  = 0x80 
        IncrementActionStr = __increment_actions_for_utf8
    elif Setup.buffer_codec_transformation_info == "utf16-state-split":
        LowestRangeBorder  = 0x10000 
        IncrementActionStr = __increment_actions_for_utf16
    else:
        return None

    # (*) If all but the last interval are exclusively below 0x80, then the 
    #     'easy default utf*' can be applied. 

    # 'last_but_one.end == last.begin', because all intervals are adjacent.
    if tm[-1][0].begin >= LowestRangeBorder: return None

    # The last interval lies beyond the border and has a common action
    # Only add the additional increment instructions.
    tm[-1] = (tm[-1][0], deepcopy(tm[-1][1]))
    tm[-1][1].extend(IncrementActionStr)

    # (*) The first interval may start at - sys.maxint
    if tm[0][0].begin < 0: tm[0][0].begin = 0

    # Later interval shall not!
    assert tm[0][0].end > 0

    # Code the transition map
    return _transition_map_coder_do(tm, BeforeGotoReloadAction=None, UponReloadDoneAdr=None)

def _transition_map_coder_do(TM, BeforeGotoReloadAction, UponReloadDoneAdr):

    LanguageDB = Setup.language_db

    txt = []
    if BeforeGotoReloadAction is not None:
        assert isinstance(UponReloadDoneAdr, (int, long))
        engine_type = engine.FORWARD
        #index = transition_map_tool.index(TransitionMap, Setup.buffer_limit_code)
        #assert index is not None
        #assert TransitionMap[index][1] == E_StateIndices.DROP_OUT
        goto_reload_action = copy(BeforeGotoReloadAction)
        goto_reload_action.append(LanguageDB.GOTO_RELOAD(UponReloadDoneAdr, True, engine_type))
        goto_reload_str    = "".join(goto_reload_action)
        transition_map_tool.set(TM, Setup.buffer_limit_code, goto_reload_str)
    else:
        engine_type     = engine.CHARACTER_COUNTER
        goto_reload_str = None

    # The range of possible characters may be restricted. It must be ensured,
    # that the occurring characters only belong to the admissible range.
    transition_map_tool.prune(TM, 0, Setup.get_character_value_limit())

    TransitionCodeFactory.init(engine_type, 
                               StateIndex    = None,
                               InitStateF    = True,
                               GotoReloadStr = goto_reload_str,
                               TheAnalyzer   = None)
    tm = [ 
        (interval, TransitionCodeFactory.do(x)) for interval, x in TM 
    ]

    LanguageDB.code_generation_switch_cases_add_statement("break;")
    transition_block.do(txt, tm)
    LanguageDB.code_generation_switch_cases_add_statement(None)

    txt.append(0)
    txt.append(LanguageDB.INPUT_P_INCREMENT())
    txt.append("\n")

    return txt

def replace_iterator_name(txt, IteratorName, StateMachineF):
    def replacer(block, StateMachineF):
        if block.find("(me->buffer._input_p)") != -1: 
            block = block.replace("(me->buffer._input_p)", IteratorName)
        if not StateMachineF:
            block = Match_input.sub("(*%s)" % IteratorName, block)
            block = Match_iterator.sub("(%s)" % IteratorName, block)
        return block

    for i, elm in enumerate(txt):
        if not isinstance(elm, (str, unicode)): continue
        txt[i] = replacer(elm, StateMachineF)

    return txt

__increment_actions_for_utf8 = [
     1, "if     ( ((*iterator) & 0x80) == 0 ) { iterator += 1; } /* 1byte character */\n",
     1, "/* NOT ( ((*iterator) & 0x40) == 0 ) { iterator += 2; }    2byte character */\n",
     1, "else if( ((*iterator) & 0x20) == 0 ) { iterator += 2; } /* 2byte character */\n",
     1, "else if( ((*iterator) & 0x10) == 0 ) { iterator += 3; } /* 3byte character */\n",
     1, "else if( ((*iterator) & 0x08) == 0 ) { iterator += 4; } /* 4byte character */\n",
     1, "else if( ((*iterator) & 0x04) == 0 ) { iterator += 5; } /* 5byte character */\n",
     1, "else if( ((*iterator) & 0x02) == 0 ) { iterator += 6; } /* 6byte character */\n",
     1, "else if( ((*iterator) & 0x01) == 0 ) { iterator += 7; } /* 7byte character */\n",
     1, "else                                 { iterator += 1; } /* default 1       */\n",
     1, "continue;\n"
]
    
__increment_actions_for_utf16 = [
     1, "if( *iterator >= 0xD800 && *iterator < 0xE000 ) {\n",
     2, "iterator += 2; continue; /* 2chunk character */\n",
     1, "}\n",
]
    
