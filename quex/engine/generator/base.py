# (C) Frank Rene Schaefer
from   quex.engine.misc.file_in                        import error_msg
import quex.engine.generator.state_machine_coder       as     state_machine_coder
import quex.engine.generator.state_router              as     state_router_generator
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.analyzer.door_id_address_label      import DoorID, \
                                                              IfDoorIdReferencedCode, \
                                                              get_plain_strings, \
                                                              dial_db
import quex.engine.state_machine.parallelize           as     parallelize
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
import quex.engine.state_machine.index                 as     index
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.transformation        as     transformation
from   quex.engine.generator.state.transition.code     import TransitionCodeFactory
import quex.engine.generator.state.transition.core     as     transition_block
import quex.engine.generator.reload_state              as     reload_state_coder
import quex.engine.analyzer.engine_supply_factory      as     engine
from   quex.engine.analyzer.terminal.core              import Terminal
from   quex.engine.analyzer.transition_map             import TransitionMap
import quex.engine.analyzer.core                       as     analyzer_generator
from   quex.engine.analyzer.state.core                 import ReloadState
import quex.engine.analyzer.engine_supply_factory      as     engine_supply_factory
from   quex.engine.interval_handling                   import NumberSet, Interval, NumberSet_All
from   quex.input.files.counter_db                     import CounterDB, \
                                                              CounterCoderData
from   quex.input.files.counter_setup                  import LineColumnCounterSetup_Default
from   quex.input.regular_expression.construct         import Pattern
import quex.output.cpp.counter_for_pattern             as     counter_for_pattern

from   quex.engine.tools                               import all_isinstance, \
                                                              none_is_None, \
                                                              typed
from   quex.blackboard import E_IncidenceIDs, \
                              E_StateIndices, \
                              E_MapImplementationType, \
                              setup as Setup, \
                              Lng

from   itertools   import ifilter
from   copy        import copy, deepcopy
from   collections import defaultdict


class EngineStateMachineSet:
    def __init__(self, PatternList): 
        assert isinstance(PatternList, list)
        assert all_isinstance(PatternList, Pattern)

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

# MAIN:      sm --> analyzer
#            sm_txt --> code_analyzer
#            terminal_txt --> code_terminals
#
# PRE_SM:    pre_sm --> analyzer
#            pre_sm_txt --> code_analyzer
#            terminal = begin of core
#
# BIPD_SM-s: bipd_sm -> analyzer
#            bipd_sm_txt -> code_analyzer
#            termina = terminal for which BIPD operated
#
# COUNT_SM:  count_db --> count_sm
#            analyzer  = get_analyzer
#            modify analyzer
#            terminal = exit_door_id
#
# SKIPER_SM:
#
# RANGE_SKIPPER_SM:
#
# NESTER_RANGE_SKIPPER_SM:
#
# INDENTATION_DETECTOR_SM:

def do_main(SM, BipdEntryDoorIdDb):
    """Main pattern matching state machine (forward).
    ---------------------------------------------------------------------------
    Micro actions are: line/column number counting, position set/reset,
    last acceptance setting/reset, lexeme start pointer set/reset, setting
    terminating zero for lexeme/reset, setting last character. 

            DropOut     --> FAILURE
            BLC         --> ReloadStateForward
            EndOfStream --> END_OF_STREAM

    Variables (potentially) required:

            position, PositionRegisterN, last_acceptance, input.
    """
    txt, analyzer = do_state_machine(SM, engine.Class_FORWARD(BipdEntryDoorIdDb))

    # Number of different entries in the position register map
    position_register_n = len(set(analyzer.position_register_map.itervalues()))
    # Position registers
    if position_register_n == 0:
        variable_db.require("position",          Initial = "(void*)0x0", Type = "void*")
        variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % position_register_n)
    else:
        variable_db.require_array("position", ElementN = position_register_n,
                                  Initial  = "{ " + ("0, " * (position_register_n - 1) + "0") + "}")
        variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % position_register_n)

    if analyzer.last_acceptance_variable_required():
        variable_db.require("last_acceptance")

    return txt, analyzer.reload_state

def do_pre_context(SM, PreContextSmIdList):
    """Pre-context detecting state machine (backward).
    ---------------------------------------------------------------------------
    Micro actions are: pre-context fullfilled_f

            DropOut     --> Begin of 'main' state machine.
            BLC         --> ReloadStateBackward
            EndOfStream --> 'error'

    Variables (potentially) required:

            pre_context_fulfilled_f[N] --> Array of flags for pre-context
                                           indication.
    RETURNS: [0] generated code text
             [1] reload state BACKWARD, to be generated later.
    """

    if SM is None: 
        return [], None

    txt, analyzer = do_state_machine(SM, engine.BACKWARD_PRE_CONTEXT) 

    txt.append("\n%s:" % dial_db.get_label_by_door_id(DoorID.global_end_of_pre_context_check()))
    # -- set the input stream back to the real current position.
    #    during backward lexing the analyzer went backwards, so it needs to be reset.
    txt.append("    %s\n" % Lng.INPUT_P_TO_LEXEME_START())

    for sm_id in PreContextSmIdList:
        variable_db.require("pre_context_%i_fulfilled_f", Index = sm_id)

    return txt, analyzer.reload_state

def do_backward_input_position_detectors(BipdDb):
    result = []
    bipd_entry_door_id_db = {}
    for incidence_id, bipd_sm in BipdDb.iteritems():
        txt, analyzer = do_state_machine(bipd_sm, engine.Class_BACKWARD_INPUT_POSITION(incidence_id)) 
        bipd_entry_door_id_db[incidence_id] = analyzer.get_action_at_state_machine_entry().door_id
        result.extend(txt)
    return result, bipd_entry_door_id_db

def do_reload_procedures(ReloadForwardState, ReloadBackwardState):
    """Lazy (delayed) code generation of the forward and backward reloaders. 
    Any state who needs reload may 'register' in a reloader. This registering may 
    happen after the code generation of forward or backward state machine.
    """
    # Variables that tell where to go after reload success and reload failure
    if Setup.buffer_based_analyzis_f:               
        return

    txt = []
    if ReloadForwardState is not None:
        txt.extend(reload_state_coder.do(ReloadForwardState))
    if ReloadBackwardState is not None:
        txt.extend(reload_state_coder.do(ReloadBackwardState))

    variable_db.require("target_state_else_index")  # upon reload failure
    variable_db.require("target_state_index")       # upon reload success

    return txt

def do_state_router():
    routed_address_set = dial_db.routed_address_set()
    # If there is only one address subject to state routing, then the
    # state router needs to be implemented.
    #if len(routed_address_set) == 0:
    #    return []

    # Add the address of 'terminal_end_of_file()' if it is not there, already.
    # (It should: assert address_eof in routed_address_set
    address_eof        = dial_db.get_address_by_door_id(DoorID.incidence(E_IncidenceIDs.END_OF_STREAM)) 
    routed_address_set.add(address_eof)
    dial_db.mark_label_as_gotoed(dial_db.get_label_by_address(address_eof))

    routed_state_info_list = state_router_generator.get_info(routed_address_set)
    return state_router_generator.do(routed_state_info_list) 

def do_variable_definitions():
    # Target state index
    variable_db.require("target_state_index", Condition_ComputedGoto=False) 

    # Following function refers to the global 'variable_db'
    return Lng.VARIABLE_DEFINITIONS(variable_db)

def do_state_machine(sm, EngineType): 
    assert len(sm.get_orphaned_state_index_list()) == 0
    

    txt = []
    # -- [optional] comment state machine transitions 
    if Setup.comment_state_machine_f: 
        Lng.COMMENT_STATE_MACHINE(txt, sm)

    # -- implement the state machine itself
    analyzer = analyzer_generator.do(sm, EngineType)
    return do_analyzer(analyzer), analyzer

def do_analyzer(analyzer): 
    

    state_machine_code = state_machine_coder.do(analyzer)
    Lng.REPLACE_INDENT(state_machine_code)
    # Variable to store the current input
    variable_db.require("input") 
    return state_machine_code

@typed(TerminalList=[Terminal])
def do_terminals(TerminalList, SimpleF=False):
    lexeme_macro_definition_str = ""
    if not SimpleF:
        lexeme_macro_definition_str = Lng.TERMINAL_LEXEME_MACRO_DEFINITIONS()
    txt = [ lexeme_macro_definition_str ]
    txt.extend(Lng.TERMINAL_CODE(TerminalList))
    return txt

def do_reentry_preparation(PreContextSmIdList, TerminalDb):
    
    return Lng.REENTRY_PREPARATION(PreContextSmIdList, 
                                  TerminalDb.get(E_IncidenceIDs.AFTER_MATCH))

def do_loop(CounterDb, AfterExitDoorId, CharacterSet=None, CheckLexemeEndF=False, ReloadF=False, GlobalReloadState=None):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop
    """
    assert CharacterSet is None or isinstance(CharacterSet, NumberSet)

    if CharacterSet is None:
        CharacterSet = NumberSet_All()

    ccd                     = CounterCoderData(CounterDb, CharacterSet, AfterExitDoorId)
    analyzer, exit_terminal = ccd.get_analyzer(engine.CHARACTER_COUNTER, GlobalReloadState, CheckLexemeEndF=CheckLexemeEndF)

    code                    = state_machine_coder.do(analyzer)

    code.extend(do_terminals([exit_terminal], SimpleF=True))

    if ReloadF and not GlobalReloadState:
        reload_code = Generator.code_reload_procedures(analyzer.reload_state, None)
        code.extend(reload_code)
        variable_db.require("position",          Initial = "(void*)0x0", Type = "void*")
        variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % 0)

    variable_db.require("input") 
    # Upon reload, the reference pointer may have to be added. When the reload is
    # done the reference pointer needs to be reset. 
    if ccd.column_count_per_chunk is not None:
        variable_db.require("reference_p")

    return code

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
    
