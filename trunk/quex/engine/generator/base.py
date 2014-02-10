# (C) Frank Rene Schaefer
from   quex.engine.misc.file_in                        import error_msg
import quex.engine.terminal_map                        as     terminal_map
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
from   quex.engine.analyzer.commands                   import CommandList
from   quex.engine.analyzer.state.core                 import ReloadState
from   quex.engine.analyzer.state.drop_out             import DropOutGotoDoorId
from   quex.engine.analyzer.state.entry_action         import TransitionAction
import quex.engine.analyzer.engine_supply_factory      as     engine_supply_factory
from   quex.engine.interval_handling                   import NumberSet, Interval, NumberSet_All
from   quex.input.regular_expression.construct         import Pattern
import quex.output.cpp.counter_for_pattern             as     counter_for_pattern

from   quex.engine.tools                               import all_isinstance, \
                                                              all_true, \
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

    if analyzer.last_acceptance_variable_required():
        variable_db.require("last_acceptance")

    return txt, analyzer

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

    variable_db.require("input") 

    return txt, analyzer

def do_backward_input_position_detectors(BipdDb):
    result = []
    bipd_entry_door_id_db = {}
    for incidence_id, bipd_sm in BipdDb.iteritems():
        txt, analyzer = do_state_machine(bipd_sm, engine.Class_BACKWARD_INPUT_POSITION(incidence_id)) 
        bipd_entry_door_id_db[incidence_id] = analyzer.get_action_at_state_machine_entry().door_id
        result.extend(txt)
    return result, bipd_entry_door_id_db

def do_reload_procedure(TheAnalyzer):
    """Lazy (delayed) code generation of the forward and backward reloaders. 
    Any state who needs reload may 'register' in a reloader. This registering may 
    happen after the code generation of forward or backward state machine.
    """
    # Variables that tell where to go after reload success and reload failure
    if Setup.buffer_based_analyzis_f:       return []

    if   TheAnalyzer is None:                                  return []
    elif TheAnalyzer.engine_type.is_BACKWARD_INPUT_POSITION(): return []
    elif TheAnalyzer.reload_state is None:                     return []
    elif TheAnalyzer.reload_state_extern_f:                    return []

    variable_db.require("target_state_else_index")  # upon reload failure
    variable_db.require("target_state_index")       # upon reload success

    # Number of different entries in the position register map
    # Position registers
    if TheAnalyzer.position_register_map is None:
        position_register_n = 0
    else:
        position_register_n = len(set(TheAnalyzer.position_register_map.itervalues()))

    if position_register_n == 0:
        if not Setup.buffer_based_analyzis_f:
            # Not 'buffer-only-mode' => reload requires at least dummy parameters.
            variable_db.require_array("position", ElementN = 0,
                                      Initial = "(void*)0x0")
            variable_db.require("PositionRegisterN", 
                                Initial = "(size_t)%i" % position_register_n)
    else:
        variable_db.require_array("position", ElementN = position_register_n,
                                  Initial  = "{ " + ("0, " * (position_register_n - 1) + "0") + "}")
        variable_db.require("PositionRegisterN", 
                            Initial = "(size_t)%i" % position_register_n)

    return reload_state_coder.do(TheAnalyzer.reload_state)

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
    analyzer_generator.prepare_reload(analyzer)
    sm_text  = do_analyzer(analyzer)
    txt.extend(sm_text)
    return txt, analyzer

def do_analyzer(analyzer): 
    

    state_machine_code = state_machine_coder.do(analyzer)
    Lng.REPLACE_INDENT(state_machine_code)
    # Variable to store the current input
    variable_db.require("input") 
    return state_machine_code

@typed(TerminalList=[Terminal])
def do_terminals(TerminalList, TheAnalyzer):
    return Lng.TERMINAL_CODE(TerminalList, TheAnalyzer)

def do_reentry_preparation(PreContextSmIdList, OnAfterMatchCode):
    return Lng.REENTRY_PREPARATION(PreContextSmIdList, OnAfterMatchCode)

@typed(CharacterSet=(None, NumberSet), ReloadF=bool, LexemeEndCheckF=bool, DoorIdExit=DoorID)
def do_loop(CounterDb, DoorIdExit, CharacterSet=None, LexemeEndCheckF=False, ReloadF=False, ReloadStateExtern=None):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop

       NOTE: This function does NOT code the FAILURE terminal. The caller needs to 
             do this if required.
    """
    assert ReloadF or ReloadStateExtern is None

    if CharacterSet is None:
        CharacterSet = NumberSet_All()

    # (*) Construct State Machine and Terminals _______________________________
    #
    # -- The state machine / analyzer
    ccfactory        = CounterDb.get_factory(CharacterSet, Lng.INPUT_P())
    incidence_id_map = ccfactory.get_incidence_id_map()
    reference_p_f    = ccfactory.requires_reference_p()

    sm,            \
    on_entry,      \
    on_reentry,    \
    terminal_else  = terminal_map.do(incidence_id_map, ReloadF, DoorIdExit)

    analyzer = analyzer_generator.do(sm, engine.FORWARD, ReloadStateExtern)
    analyzer.init_state().drop_out = DropOutGotoDoorId(DoorIdExit)

    if ReloadF:
        on_before_reload_0  = ccfactory.get_on_before_reload()
        on_after_reload_0   = ccfactory.get_on_after_reload()
        on_before_reload_1, \
        on_after_reload_1   = terminal_map.get_before_and_after_reload()
        on_before_reload    = CommandList.from_iterable(on_before_reload_0 + on_before_reload_1)
        on_after_reload     = CommandList.from_iterable(on_after_reload_0  + on_after_reload_1)

        analyzer_generator.prepare_reload(analyzer_generator, ReloadStateExtern,
                                          on_before_reload, on_after_reload)

    # -- The terminals 
    #
    if not LexemeEndCheckF: door_id_on_lexeme_end = None
    else:                   door_id_on_lexeme_end = DoorIdExit

    # DoorID of reentry:
    entry           = analyzer.init_state().entry
        
    # OnEntry
    ta_on_entry = entry.get_action(sm.init_state_index, E_StateIndices.NONE)
    ta_on_entry.command_list = CommandList.concatinate(ta_on_entry.command_list, 
                                                       on_entry)

    # OnReEntry
    transition_id   = entry.enter(sm.init_state_index, index.get(), 
                                  TransitionAction(CommandList.from_iterable(on_reentry)))
    entry.categorize(sm.init_state_index)
    door_id_reentry = entry.get(transition_id).door_id

    terminal_list   = ccfactory.get_terminal_list(Lng.INPUT_P(), 
                                                  DoorIdOk=door_id_reentry, 
                                                  DoorIdOnLexemeEnd=door_id_on_lexeme_end)
    terminal_list.append(terminal_else)

    # (*) Generate Code _______________________________________________________
    txt_main             = do_analyzer(analyzer)
    assert all_isinstance(txt_main, (IfDoorIdReferencedCode, int, str, unicode))
    txt_terminals        = do_terminals(terminal_list, analyzer)
    assert all_isinstance(txt_terminals, (IfDoorIdReferencedCode, int, str, unicode))

    if ReloadF:
        txt_reload_procedure = do_reload_procedure(analyzer)
        assert all_isinstance(txt_reload_procedure, (IfDoorIdReferencedCode, int, str, unicode))

    txt = []
    txt.extend(txt_main)
    txt.extend(txt_terminals)
    if ReloadF:
        txt.extend(txt_reload_procedure)

    if reference_p_f:
        variable_db.require("reference_p")

    return txt, DoorID.incidence(terminal_else.incidence_id())

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
    
