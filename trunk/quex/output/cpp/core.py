# (C) Frank-Rene Schaefer
#______________________________________________________________________________
from   quex.engine.generator.languages.variable_db import variable_db
from   quex.engine.analyzer.door_id_address_label  import IfDoorIdReferencedCode, \
                                                          get_plain_strings
from   quex.engine.analyzer.terminal.core          import Terminal
from   quex.engine.generator.base                  import EngineStateMachineSet
import quex.engine.generator.base                  as     generator
from   quex.engine.tools                           import all_isinstance, typed
from   quex.input.regular_expression.construct     import Pattern
from   quex.input.files.counter_db                 import CounterDB
import quex.output.cpp.counter                     as     counter
from   quex.blackboard                             import setup as Setup, \
                                                          E_IncidenceIDs, \
                                                          E_TerminalType, \
                                                          Lng

@typed(ModeNameList = [(str, unicode)])
def do(Mode, ModeNameList):
    """RETURNS: The analyzer code for a mode defined in 'Mode'.
    """
    # (*) Initialize address handling
    variable_db.init()  # because constructor creates some addresses.

    function_body,       \
    variable_definitions = do_core(Mode.pattern_list, 
                                   Mode.terminal_db,
                                   Mode.on_after_match_code)

    function_txt = wrap_up(Mode.name, function_body, variable_definitions, 
                           ModeNameList)

    # (*) Generate the counter first!
    #     (It may implement a state machine with labels and addresses
    #      which are not relevant for the main analyzer function.)
    counter_txt = []
    if Mode.default_character_counter_required_f:
        variable_db.init()  # because constructor creates some addresses.
        counter_txt = do_default_counter(Mode.name, Mode.counter_db)

    return counter_txt + function_txt

@typed(PatternList=[Pattern], TerminalDb={(E_IncidenceIDs, long): Terminal})
def do_core(PatternList, TerminalDb, OnAfterMatchCode=None):
    """Produces main code for an analyzer function which can detect patterns given in
    the 'PatternList' and has things to be done mentioned in 'TerminalDb'. 

    RETURN: Code implementing the lexical analyzer.

    The code is not embedded in a function and required definitions are not provided.
    This happens through function 'wrap_up()'.
    """
    # Prepare the combined state machines and terminals 
    esms = EngineStateMachineSet(PatternList)

    # (*) Pre Context State Machine
    #     (If present: All pre-context combined in single backward analyzer.)
    pre_context, \
    pre_analyzer          = generator.do_pre_context(esms.pre_context_sm,
                                                     esms.pre_context_sm_id_list)

    # assert all_isinstance(pre_context, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Backward input position detection
    #     (Seldomly present -- only for Pseudo-Ambiguous Post Contexts)
    bipd, \
    bipd_entry_door_id_db = generator.do_backward_input_position_detectors(esms.bipd_sm_db)
    # assert all_isinstance(bipd, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Main State Machine -- try to match core patterns
    #     Post-context handling is webbed into the main state machine.
    main, \
    main_analyzer         = generator.do_main(esms.sm, bipd_entry_door_id_db)
    # assert all_isinstance(main, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Terminals
    #     (BEFORE 'Reload procedures' because some terminals may add entries
    #      to the reloader.)
    terminals             = generator.do_terminals(TerminalDb.values(), 
                                                   main_analyzer)

    # (*) Reload procedures
    reload_procedures     = generator.do_reload_procedures(main_analyzer, 
                                                           pre_analyzer)
    # assert all_isinstance(reload_procedures, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Re-entry preparation
    reentry_prerpation    = generator.do_reentry_preparation(esms.pre_context_sm_id_list,
                                                             OnAfterMatchCode)

    # (*) State Router
    #     (Something that can goto a state address by an given integer value)
    state_router          = generator.do_state_router()
    # assert all_isinstance(state_router, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Variable Definitions
    #     (Code that defines all required variables for the analyzer)
    variable_definitions  = generator.do_variable_definitions()
    # assert all_isinstance(variable_definitions, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Putting it all together
    function_body = []
    function_body.extend(pre_context)         # implementation of pre-contexts (if there are some)
    function_body.extend(main)                # main pattern matcher
    function_body.extend(bipd)                # (seldom != empty; only for pseudo-ambiguous post contexts)
    function_body.extend(terminals)           
    function_body.extend(state_router)        # route to state by index (only if no computed gotos)
    function_body.extend(reload_procedures)
    function_body.extend(reentry_prerpation)   

    return function_body, variable_definitions

def wrap_up(ModeName, FunctionBody, VariableDefs, ModeNameList):
    txt_function = Lng.ANALYZER_FUNCTION(ModeName, Setup, VariableDefs, 
                                         FunctionBody, ModeNameList) 
    txt_header   = Lng.HEADER_DEFINITIONS() 
    assert isinstance(txt_header, (str, unicode))

    txt_analyzer = get_plain_strings(txt_function)
    assert all_isinstance(txt_analyzer, (str, unicode))

    return [ txt_header ] + txt_analyzer

@typed(ModeName=(str,unicode), CounterDb=CounterDB)
def do_default_counter(ModeName, CounterDb):
    # May be, the default counter is the same as for another mode. In that
    # case call the default counter of the other mode with the same one and
    # only macro.
    default_character_counter_function_name,   \
    default_character_counter_function_code  = counter.get(CounterDb, ModeName)

    txt = [ Lng.DEFAULT_COUNTER_PROLOG(default_character_counter_function_name) ]

    if default_character_counter_function_code is not None:
        txt.append(default_character_counter_function_code)

    return txt

def frame_this(Code):
    return Lng["$frame"](Code, Setup)


