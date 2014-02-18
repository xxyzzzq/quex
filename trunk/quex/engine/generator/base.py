# (C) Frank Rene Schaefer
from   quex.engine.misc.file_in                        import error_msg
import quex.engine.generator.state_machine_coder       as     state_machine_coder
import quex.engine.generator.state_router              as     state_router_generator
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.code.core                 import CodeTerminal
from   quex.engine.analyzer.door_id_address_label      import DoorID, \
                                                              IfDoorIdReferencedCode, \
                                                              get_plain_strings, \
                                                              dial_db
import quex.engine.state_machine.index                 as     index
from   quex.engine.state_machine.core                  import StateMachine
from   quex.engine.state_machine.engine_state_machine_set import CharacterSetStateMachine
import quex.engine.state_machine.transformation        as     transformation
from   quex.engine.generator.state.transition.code     import TransitionCodeFactory
import quex.engine.generator.state.transition.core     as     transition_block
import quex.engine.generator.reload_state              as     reload_state_coder
import quex.engine.analyzer.engine_supply_factory      as     engine
from   quex.engine.analyzer.terminal.core              import Terminal
from   quex.engine.analyzer.transition_map             import TransitionMap
import quex.engine.analyzer.core                       as     analyzer_generator
from   quex.engine.analyzer.commands                   import CommandList, \
                                                              GotoDoorId
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
                                                              print_callstack, \
                                                              typed
from   quex.blackboard import E_IncidenceIDs, \
                              E_StateIndices, \
                              E_MapImplementationType, \
                              setup as Setup, \
                              Lng

from   copy        import copy, deepcopy
from   collections import defaultdict


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

    require_position_registers(TheAnalyzer)

    return reload_state_coder.do(TheAnalyzer.reload_state)

def require_position_registers(TheAnalyzer):
    """Require an array to store input positions. This has later to be 
    implemented as 'variables'. Position registers are exclusively used
    for post-context restore. No other engine than FORWARD would require
    those.
    """
    if not TheAnalyzer.engine_type.is_FORWARD(): 
        return

    if TheAnalyzer.position_register_map is None:
        position_register_n = 0
    else:
        position_register_n = len(set(TheAnalyzer.position_register_map.itervalues()))

    if position_register_n != 0:
        initial_array  = "{ " + ("0, " * (position_register_n - 1) + "0") + "}"
    else:
        # Implement a dummy array (except that there is no reload)
        if Setup.buffer_based_analyzis_f: return
        initial_array = "(void*)0"

    variable_db.require_array("position", ElementN = position_register_n,
                              Initial = initial_array)
    variable_db.require("PositionRegisterN", 
                        Initial = "(size_t)%i" % position_register_n)

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
    assert CounterDb.covered_character_set().covers_range(0, Setup.get_character_value_limit()), \
           "CounterDb covers %s\nbut, not all of [0, %s]" \
           % (CounterDb.covered_character_set(), Setup.get_character_value_limit())

    def prepare_entry_and_reentry(analyzer, on_begin):
        """Prepare the entry and re-entry doors into the initial state
        of the loop-implementing initial state.

                       .----------.
                       | on_entry |
                       '----------'
                            |         .------------.
                            |<--------| on_reentry |<-----.
                            |         '------------'      |
                    .----------------.                    |
                    |                +-----> Terminal ----+----> Exit
                    |      ...       |
                    |                +-----> Terminal - - 
                    '----------------'

           RETURNS: DoorID of the re-entry door which is used to iterate in 
                    the loop.
        """
        # Entry into state machine
        entry = analyzer.init_state().entry
        init_state_index = analyzer.init_state_index
            
        # OnEntry
        ta_on_entry = entry.get_action(init_state_index, E_StateIndices.NONE)
        ta_on_entry.command_list = CommandList.concatinate(ta_on_entry.command_list, 
                                                           on_begin)

        # OnReEntry
        tid_reentry = entry.enter(init_state_index, index.get(), 
                                  TransitionAction(CommandList.from_iterable(on_begin)))
        entry.categorize(init_state_index)

        return entry.get(tid_reentry).door_id

    def prepare_reload(analyzer, ccfactory, cssm, ReloadStateExtern): 
        on_before_reload = CommandList.from_iterable(
              ccfactory.on_before_reload
            + cssm.on_before_reload
        )
        on_after_reload  = CommandList.from_iterable(
              ccfactory.on_after_reload
            + cssm.on_after_reload
        )

        analyzer_generator.prepare_reload(analyzer, on_before_reload, on_after_reload)

    if CharacterSet is None:
        CharacterSet = NumberSet_All()

    # (*) Construct State Machine and Terminals _______________________________
    #
    # -- The state machine / analyzer
    ccfactory        = CounterDb.get_factory(CharacterSet, Lng.INPUT_P())
    incidence_id_map = ccfactory.get_incidence_id_map()
    reference_p_f    = ccfactory.requires_reference_p()

    beyond_iid = dial_db.new_incidence_id()
    beyond_set = CharacterSet.inverse().mask(0, Setup.get_character_value_limit())
    incidence_id_map.append((beyond_set, beyond_iid))

    cssm = CharacterSetStateMachine(incidence_id_map)

    analyzer = analyzer_generator.do(cssm.sm, engine.FORWARD, ReloadStateExtern)
    analyzer.init_state().drop_out = DropOutGotoDoorId(DoorIdExit)

    door_id_reentry = prepare_entry_and_reentry(analyzer, cssm.on_begin) 

    if not LexemeEndCheckF: door_id_on_lexeme_end = None
    else:                   door_id_on_lexeme_end = DoorIdExit

    # -- Analyzer: Prepare Reload
    if ReloadF:
        prepare_reload(analyzer, ccfactory, cssm, ReloadStateExtern)

    # -- The terminals 
    #
    terminal_list   = ccfactory.get_terminal_list(Lng.INPUT_P(), 
                                                  DoorIdOk          = door_id_reentry, 
                                                  DoorIdOnLexemeEnd = door_id_on_lexeme_end)
    on_beyond       = cssm.on_putback + [ GotoDoorId(DoorIdExit) ]
    code_on_beyond  = CodeTerminal([Lng.COMMAND(cmd) for cmd in on_beyond])
    terminal_beyond = Terminal(code_on_beyond, "<BEYOND>") # Put last considered character back
    terminal_beyond.set_incidence_id(beyond_iid)
    terminal_list.append(terminal_beyond)

    # (*) Generate Code _______________________________________________________
    txt = []
    txt.extend(do_analyzer(analyzer))
    txt.extend(do_terminals(terminal_list, analyzer))
    if ReloadF:
        txt.extend(do_reload_procedure(analyzer))

    if reference_p_f:
        variable_db.require("reference_p")

    return txt, DoorID.incidence(terminal_beyond.incidence_id())

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
    
