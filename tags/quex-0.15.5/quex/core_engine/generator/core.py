import quex.core_engine.state_machine.parallelize     as parallelize
import quex.core_engine.generator.languages.core      as languages
import quex.core_engine.generator.state_machine_coder as state_machine_coder
#
from quex.core_engine.generator.action_info import ActionInfo

def do(PatternActionPair_List, DefaultAction, Language="C++", StateMachineName="",
       PrintStateMachineF=False,
       AnalyserStateClassName="analyser_state",
       StandAloneAnalyserF=False,
       PatternDictionary={},
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
    assert type(PatternActionPair_List) == list
    assert map(lambda elm: elm.__class__.__name__ == "ActionInfo", PatternActionPair_List) \
           == [ True ] * len(PatternActionPair_List)
    assert StandAloneAnalyserF or QuexEngineHeaderDefinitionFile != "", \
           "Non-Stand-Alone Lexical Analyser cannot be created without naming explicitly\n" + \
           "a header file for the core engine define statements. See file\n" + \
           "$QUEX_DIR/code_base/core_engine/definitions-plain-memory.h for an example"       

    if QuexEngineHeaderDefinitionFile == "":
        QuexEngineHeaderDefinitionFile = "core_engine/definitions-plain-memory.h" 
    
    # (0) extract data structures:
    #      -- state machine list: simply a list of all state machines
    #         (the original state machine id is marked as 'origin' inside 
    #          'get_state_machine')
    #      -- a map from state machine id to related action (i.e. the code fragment) 
    state_machine_list = []
    action_db          = {}
    
    # -- extract:
    #    -- state machines that are post-conditioned
    post_conditioned_sm_id_list = []
    #    -- state machines that nore non-trivially pre-conditioned, 
    #       i.e. they need a reverse state machine to be verified.
    pre_condition_sm_id_list  = []
    pre_condition_sm_list     = []
    #    -- pre-conditions that are trivial, i.e. it is only checked for
    #       the last character, if it was a particular one or not.
    begin_of_line_condition_f = False
    # [NOT IMPLEMENTED YET]    
    # # trivial_pre_condition_dict = {}             # map: state machine id --> character code(s)
    for action_info in PatternActionPair_List:
        sm = action_info.pattern_state_machine()
        state_machine_list.append(sm)
        # -- register action information under the state machine id, where it 
        #    belongs.
        origins_of_acceptance_states = sm.get_origin_ids_of_acceptance_states()
        assert len(origins_of_acceptance_states) != 0, \
               "error: code generation for pattern:\n" + \
               "error: no acceptance state contains origin information."
        origin_state_machine_id = origins_of_acceptance_states[0]
        action_db[origin_state_machine_id] = action_info

        # -- collect all pre-conditions and make one single state machine out of it
        if sm.has_non_trivial_pre_condition():
            pre_sm = sm.pre_condition_state_machine
            pre_condition_sm_list.append(pre_sm)
            pre_condition_sm_id_list.append(pre_sm.get_id())
            
        if sm.has_trivial_pre_condition_begin_of_line():
            begin_of_line_condition_f = True

        # [NOT IMPLEMENTED YET]    
        # # -- collect information about trivial (char code) pre-conditions 
        # # if sm.get_trivial_pre_condition_character_codes() != []:
        # #    trivial_pre_condition_dict[sm.get_id()] = sm.get_trivial_pre_condition_character_codes()

        # -- collect all ids of post conditioned state machines
        if sm.is_post_conditioned():
            post_conditioned_sm_id_list.append(origin_state_machine_id)
                                    
    # (1) transform all given patterns into a single state machine
    #     (the index of the patterns remain as 'origins' inside the states)
    sm = get_state_machine(state_machine_list)
    #     -- check for the 'nothing is fine' problem
    __check_for_nothing_is_fine(sm, EndOfFile_Code)


    # -- add actions for the pre-condition terminal states:
    #    (empty, because the flag 'pre_condition_fulfilled' is raised when the 
    #     acceptance state is entered)
    pre_condition_sm = None
    if pre_condition_sm_list != []:
        pre_condition_sm = get_state_machine(pre_condition_sm_list, FilterDominatedOriginsF=False)
        for pre_sm in pre_condition_sm_list:
            action_db[pre_sm.get_id()] = ActionInfo(pre_sm, "")

    # (2) create code
    return __get_code(sm, pre_condition_sm, pre_condition_sm_id_list, 
                      StateMachineName, AnalyserStateClassName, StandAloneAnalyserF, Language, 
                      pre_condition_sm_list, post_conditioned_sm_id_list, 
                      action_db, DefaultAction, begin_of_line_condition_f, 
                      QuexEngineHeaderDefinitionFile, ModeNameList, PrintStateMachineF)

def __get_code(sm, pre_condition_sm, pre_condition_sm_id_list,
               StateMachineName, AnalyserStateClassName, 
               StandAloneAnalyserF, Language,
               pre_condition_sm_list, post_conditioned_sm_id_list, 
               action_db, DefaultAction, begin_of_line_condition_f, 
               QuexEngineHeaderDefinitionFile, ModeNameList, PrintStateMachineF):

    LanguageDB = languages.db[Language]

    txt = ""
    #  -- all state machine transitions 
    if pre_condition_sm_list != []:
        txt += "    // state machine for pre-condition test:\n"
        if PrintStateMachineF: 
            txt += "    // " + repr(pre_condition_sm).replace("\n", "\n    // ") + "\n"
        txt += state_machine_coder.do(pre_condition_sm, 
                                      Language=Language, 
                                      UserDefinedStateMachineName=StateMachineName + "__PRE_CONDITION__",
                                      BackwardLexingF=True)
        
    txt += "    // state machine for pattern analysis:\n"
    if PrintStateMachineF: 
        txt += "    // " + repr(sm).replace("\n", "\n    // ") + "\n"
    txt += state_machine_coder.do(sm, Language=Language, 
                                  UserDefinedStateMachineName=StateMachineName, 
                                  BackwardLexingF=False)
    
    #  -- terminal states: execution of pattern actions  
    txt += LanguageDB["$terminal-code"](StateMachineName, sm, action_db, DefaultAction, 
                                        begin_of_line_condition_f, pre_condition_sm_id_list) 

    # -- pack the whole thing into a function 
    txt = LanguageDB["$analyser-func"](StateMachineName, AnalyserStateClassName, StandAloneAnalyserF,
                                       txt, 
                                       post_conditioned_sm_id_list, pre_condition_sm_id_list,
                                       begin_of_line_condition_f,
                                       QuexEngineHeaderDefinitionFile, 
                                       ModeNameList, InitialStateIndex=sm.init_state_index) 
    return txt
    
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

def __check_for_nothing_is_fine(sm, EndOfFile_Code):
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
    init_state = sm.states[sm.init_state_index]
    if init_state.is_acceptance() == False: 
        return

    assert False == True, \
          "error: A pattern (such as '.*' or 'x*') allows no input to be acceptable.\n" + \
          "error: This does not make sense!"

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


    
     

    


