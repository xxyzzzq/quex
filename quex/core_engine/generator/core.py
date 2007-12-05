import quex.core_engine.state_machine.parallelize     as parallelize
import quex.core_engine.generator.languages.core      as languages
import quex.core_engine.generator.languages.label     as languages_label
import quex.core_engine.generator.state_machine_coder as state_machine_coder
import quex.core_engine.generator.input_position_backward_detector as backward_detector
import quex.core_engine.generator.combined_pre_condition_state_machine as combined_pre_condition_state_machine
#
from quex.core_engine.generator.action_info import ActionInfo
from quex.core_engine.state_machine.index   import get_state_machine_by_id

class Generator:

    def __init__(self, PatternActionPair_List, EndOfFile_Code,
                 StateMachineName, AnalyserStateClassName, Language, 
                 DefaultAction, QuexEngineHeaderDefinitionFile, ModeNameList, 
                 PrintStateMachineF, StandAloneAnalyserF):

        assert type(PatternActionPair_List) == list
        assert map(lambda elm: elm.__class__.__name__ == "ActionInfo", PatternActionPair_List) \
               == [ True ] * len(PatternActionPair_List)
        if not StandAloneAnalyserF: 
            assert QuexEngineHeaderDefinitionFile != "", \
               "Non-Stand-Alone Lexical Analyser cannot be created without naming explicitly\n" + \
               "a header file for the core engine define statements. See file\n" + \
               "$QUEX_DIR/code_base/core_engine/definitions-plain-memory.h for an example"       

        if QuexEngineHeaderDefinitionFile == "":
            QuexEngineHeaderDefinitionFile = "core_engine/definitions-plain-memory.h" 
    
        self.state_machine_name                  = StateMachineName
        self.analyzer_state_class_name           = AnalyserStateClassName
        self.programming_language                = Language
        self.language_db                         = languages.db[self.programming_language]
        self.default_action                      = DefaultAction
        self.core_engine_header_definitions_file = QuexEngineHeaderDefinitionFile
        self.mode_name_list                      = ModeNameList
        self.print_state_machine_f               = PrintStateMachineF
        self.stand_alone_analyzer_f              = StandAloneAnalyserF

        # -- setup of state machine lists and id lists
        self.__extract_special_lists(PatternActionPair_List)
        # -- create combined state machines for main and pre-conditions
        self.__create_state_machines(EndOfFile_Code)
        # -- collect the state machines that help out with pseudo-ambiguous
        #    post-conditions.
        self.__collect_pseudo_ambiguous_post_condition_state_machines()

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

    def __create_state_machines(self, EndOfFile_Code):
        # (1) transform all given patterns into a single state machine
        #     (the index of the patterns remain as 'origins' inside the states)
        self.sm = get_state_machine(self.state_machine_list)
        #     -- check for the 'nothing is fine' problem
        _check_for_nothing_is_fine(self.sm, EndOfFile_Code)

        # (2) create the combined pre-condition state machine (if necessary)
        self.pre_condition_sm = None
        if self.pre_condition_sm_list != []:
            self.pre_condition_sm = get_state_machine(self.pre_condition_sm_list, 
                                                      FilterDominatedOriginsF=False)
            # -- add empty actions for the pre-condition terminal states
            for pre_sm in self.pre_condition_sm_list:
                self.action_db[pre_sm.get_id()] = ActionInfo(pre_sm, "")

    def __collect_pseudo_ambiguous_post_condition_state_machines(self):
        # -- find state machines that contain a state flagged with 
        #    'pseudo-ambiguous-post-condition'.
        papc_sm_id_list = filter(lambda backward_detector_id: backward_detector_id != -1L,
                                 map(lambda sm: sm.get_pseudo_ambiguous_post_condition_id(),
                                     self.state_machine_list))

        # -- collect all mentioned state machines in a list
        self.papc_backward_detector_state_machine_list = \
                map(get_state_machine_by_id, papc_sm_id_list)

    def __get_core_state_machine(self):
        LanguageDB = self.language_db 

        #  -- comment all state machine transitions 
        txt = "    $/* state machine $*/\n"
        if self.print_state_machine_f: 
            txt += "    $/* " + repr(self.sm).replace("\n", "$*/\n    $/* ") + "\n"
        txt += state_machine_coder.do(self.sm, 
                                      LanguageDB                  = LanguageDB, 
                                      UserDefinedStateMachineName = self.state_machine_name, 
                                      BackwardLexingF             = False)

        
        #  -- terminal states: execution of pattern actions  
        txt += LanguageDB["$terminal-code"](self.state_machine_name, 
                                            self.sm, 
                                            self.action_db, 
                                            self.default_action, 
                                            self.begin_of_line_condition_f, 
                                            self.pre_condition_sm_id_list) 

        return txt

    def __get_combined_pre_condition_state_machine(self):
        LanguageDB = self.language_db

        txt = "    $/* state machine for pre-condition test: $*/\n"
        if self.print_state_machine_f: 
            txt += "    $/* " + repr(self.pre_condition_sm).replace("\n", "$*/\n    $/* ") + "$*/\n"

        txt += state_machine_coder.do(self.pre_condition_sm, 
                                      LanguageDB                  = LanguageDB, 
                                      UserDefinedStateMachineName = self.state_machine_name + "_PRE_CONDITION_",
                                      BackwardLexingF             = True)

        LabelName = languages_label.get_terminal(self.state_machine_name + "_PRE_CONDITION_")      
        txt += "%s\n" % LanguageDB["$label-definition"](LabelName) 
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyser went backwards, so it needs to be reset.
        txt += "    QUEX_CORE_SEEK_ANALYSER_START_POSITION;\n"

        return txt

    def do(self):

        LanguageDB = self.language_db

        #  -- state machines for backward input position detection (pseudo ambiguous post conditions)
        papc_input_postion_backward_detector_functions = ""
        for sm in self.papc_backward_detector_state_machine_list:
             papc_input_postion_backward_detector_functions += backward_detector.do(sm, LanguageDB, 
                                                                                    self.print_state_machine_f) 
        function_body = ""
        # -- write the combined pre-condition state machine
        if self.pre_condition_sm_list != []:
            function_body += self.__get_combined_pre_condition_state_machine()
            
        # -- write the state machine of the 'core' patterns (i.e. no pre-conditions)
        function_body += self.__get_core_state_machine()

        # -- pack the whole thing into a function 
        analyzer_function = LanguageDB["$analyser-func"](self.state_machine_name, 
                                           self.analyzer_state_class_name, 
                                           self.stand_alone_analyzer_f,
                                           function_body, 
                                           self.post_conditioned_sm_id_list, self.pre_condition_sm_id_list,
                                           self.mode_name_list, 
                                           InitialStateIndex=self.sm.init_state_index) 

        option_str = ""
        if self.begin_of_line_condition_f: 
            option_str = LanguageDB["$compile-option"]("__QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION")

        #  -- paste the papc functions (if there are some) in front of the analyzer functions
        txt =   option_str                                                              \
              + LanguageDB["$include"](self.core_engine_header_definitions_file) + "\n" \
              + papc_input_postion_backward_detector_functions                          \
              + analyzer_function

        return languages.replace_keywords(txt, LanguageDB, NoIndentF=True)

def do(PatternActionPair_List, DefaultAction, Language="C++", StateMachineName="",
       PrintStateMachineF=False,
       AnalyserStateClassName="analyser_state",
       StandAloneAnalyserF=False,
       QuexEngineHeaderDefinitionFile="",
       ModeNameList=[],
       EndOfFile_Code=None):    
    """Contains a list of pattern-action pairs, i.e. its elements contain
       pairs of state machines and associated actions to be take,
       when a pattern matches. 

       NOTE: From this level of abstraction downwards, a pattern is 
             represented as a state machine. No longer the term pattern
             is used. The pattern to which particular states belong are
             kept track of by using an 'origin' list that contains 
             state machine ids (== pattern ids) and the original 
             state index.
             
             ** A Pattern is Identified by the State Machine ID**
       
       NOTE: It is crucial that the pattern priviledges have been entered
             into 'state_machine_id_ranking_db' in state_machine.index
             if they are to be priorized. Further, priviledged state machines
             must have been created **earlier** then lesser priviledged
             state machines.
    """
    return Generator(PatternActionPair_List, EndOfFile_Code,
                     StateMachineName, AnalyserStateClassName, Language, 
                     DefaultAction, QuexEngineHeaderDefinitionFile, ModeNameList, 
                     PrintStateMachineF, StandAloneAnalyserF).do()
    
def get_state_machine(StateMachine_List, FilterDominatedOriginsF=True):
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
    ## print "##smldfa:", sm

    # (4) determine for each state in the DFA what is the dominating original state
    if FilterDominatedOriginsF: sm.filter_dominated_origins()
    ## print "##smldfa:", sm

    # (5) perform hopcroft optimization
    #     Note, that hopcroft optimization does consider the original acceptance 
    #     states when deciding if two state sets are equivalent.   
    sm = sm.get_hopcroft_optimization()    

    return sm



def _check_for_nothing_is_fine(sm, EndOfFile_Code):
    """NOTE: This discussion is lengthy and the result is short. Please, 
             go to the end of this comment to get to the point quickly.
    
       If the state machine has an initial state that is acceptance there is a 
       very special problem. In this case, the state machine will run into an
       acceptance terminal state, even if no character matched at all. 
       
       -- Now, if the EndOfFile code character comes in, it causes a drop-out, 
       -- BUT, the last acceptance state is the initial state
       -- THUS, the state machine goes into the acceptance terminal of the 
          pattern that says 'nothing is just fine'.

       Since the pattern action related to 'nothing is just fine' does not 
       necessarily (or better very unlikely) return a token 'TERMINATION',
       the end of file would never be detected. For this reason Quex requires:

       ***    If a 'nothing is just fine' is defined, i.e. the initial state 
       ***    is an acceptance state, then the EndOfFile '<<EOF>>' must be defined
       ***   as a pattern.

       This helps, because the EndOfFile pattern is then longer than the 
       'nothing just fine' pattern, and it wins. At this point it is assumed
       that the pattern containing the 'EndOfFile' knows how to deal with it.

       NOTE: This discussion has no equivalent for backwards lexical analysis
             during pre-conditions, because it is forward analysis that moves
             the focus of the analyser. If a BeginOfFile occurs and a pre-condition
             accepts it as 'nothing is just fine' then the real analysis still
             starts at the previous end position. There is no infinit moving
             backwards in this case. THUS, this check has NOT to be accomplished
             for pre-condition state machines.

       -- The same as for EOF is true, if the condition is 'x*' for example, and
          an 'a' arrives, which shall call for a mismatch. If such a free pass is
          defined any non-matching first character **must** be defined. In the
          same way as above, this non-matching character will win and avoid 
          infinite recursion.

       FINALLY: A pattern definition of '.*' of 'x*' does not make the slightest
                sense, because we need to catch a mismatch on the first character.
                Thus the pattern must at least have a length of one. Forget about
                the whole discussion above and simply forbid pattern definitions
                with 'nothing is just fine'.
    """
    # NOTE: At this point this should never appear, since the problem is supposed
    #       to be checked against at the level of parsing the regular expression.
    init_state = sm.states[sm.init_state_index]

    assert init_state.is_acceptance() == False, \
          "error: A pattern (such as '.*' or 'x*') allows no input to be acceptable.\n" + \
          "error: This does not make sense! THIS SHOULD HAVE BEEN CHECKED AGAINST WHEN\n" + \
          "error: the state machine was created for the regular expression!"

#   That is what was necessary to implement the superflous ideas introduced in the 
#   huge comment:
#     if init_state.get_result_state_index(EndOfFile_Code) == None:
#        raise "error: A pattern (such as '.*' or 'x*') allows no input to be acceptable.\n" + \
#              "error: In this case an end of file pattern needs to be explicitly defined!" +  \
#              "error: Think about 'x+' instead of 'x*'."
#         
#     if None in init_state.get_target_state_indices() or init_state.get_epsilon_trigger_set() == []:
#       raise "error: A pattern (such as 'x*') allows no input to be acceptable. In this case\n" +         \
#             "error: another pattern (i.e. '.+') needs to catch all mismatches of the first character." + \
#             "error: Think about 'x+' instead of 'x*'."


    
     

    


