from   quex.engine.generator.languages.variable_db import variable_db
from   quex.engine.analyzer.door_id_address_label  import dial_db, IfDoorIdReferencedCode, get_plain_strings
from   quex.engine.generator.base                  import GeneratorBase
import quex.engine.generator.base                  as     generator
from   quex.engine.generator.code.core             import CodeFragment
from   quex.engine.tools                           import all_isinstance
from   quex.input.regular_expression.construct     import Pattern
import quex.output.cpp.counter                     as     counter
from   quex.blackboard                             import setup as Setup, \
                                                          E_IncidenceIDs

def do_mode(Mode, ModeNameList, IndentationSupportF, BeginOfLineSupportF):
    pattern_list = [ x.pattern for x in Mode.ppc_list ]
    terminal_db  = __prepare_terminals(Mode.ppc_list, Mode.special_terminal_list())

    core_txt, \
    default_character_counter_required_f = do(pattern_list, terminal_db, 
                                              Mode.name, ModeNameList = ModeNameList) 

    # (*) Generate the counter first!
    #     (It may implement a state machine with labels and addresses
    #      which are not relevant for the main analyzer function.)
    counter_txt = ""
    if default_character_counter_required_f:
        counter_txt = do_default_counter(Mode)

    return counter_txt + "".join(core_txt)

@typed(PPC_List=PPC, OtherTerminalCodeDb=list)
def __prepare_terminals(PPC_List, OtherTerminalCodeDb):
    """Prepare terminal states for all pattern matches and other terminals,
    such as 'end of stream' or 'failure'. If code is to be generated in a
    delayed fashion, then this may happen as a consequence to the call
    to '.get_code()' to related code fragments.

    RETURNS: 
                      map: incidence_id --> Terminal

    A terminal consists plainly of an 'incidence_id' and a list of text which
    represents the code to be executed when it is reached.
    """
    mandatory_list = [E_IncidenceIDs.FAILURE, E_IncidenceIDs.END_OF_STREAM]

    result = {}
    # Every pattern has a terminal for the case that it matches.
    for priority, pattern, code_fragment in PPC_List:
        terminal = TerminalFactory.pattern_match_terminal(pattern, code_fragment.get_code())
        assert terminal.incidence_id() not in result
        result[terminal.incidence_id()] = terminal

    # OtherTerminals: END_OF_STREAM
    #                 FAILURE
    #                 CODEC_ERROR
    #                 ...
    for incidence_id in mandatory_list:
        if incidence_id in OtherTerminalCodeDb: continue
        OtherTerminalCodeDb[incidence_id] = LanguageDB.DEFAULT_CODE_FRAGMENT(incidence_id)

    for incidence_id, code_fragment in OtherTerminalCodeDb:
        assert incidence_id not in result
        if incidence_id == E_IncidenceIDs.FAILURE:
            terminal = TerminalFactory.failure_terminal(code_fragment.get_code())
        elif incidence_id == E_IncidenceIDs.END_OF_STREAM:
            terminal = TerminalFactory.end_of_stream_terminal(code_fragment.get_code())
        else:
            terminal = TerminalFactory.plain_code_terminal(code_fragment.get_code())
        result[incidence_id] = terminal

    return result


@typed(PatternList=[Pattern], TerminalDb=dict, ModeName=(str, unicode), ModeNameList=list)
def do(PatternList, TerminalDb, ModeName, ModeNameList):
    """Produce code for an analyzer function which can detect patterns given in
    the 'PatternList' and has things to be done mentioned in 'IncidenceDb'. 

    RETURN: [0] -- Code of the function.

            [1] -- Flag indicating whether a 'default line/column counter' 
                   needs to be implemented.
    """
    assert all_isinstance(TerminalDb.itervalues(), Terminal)

    # (*) Initialize address handling
    dial_db.clear()     # BEFORE constructor of generator; 
    variable_db.init()  # because constructor creates some addresses.

    # Prepare the combined state machines and terminals 
    g = GeneratorBase(PatternList, TerminalDb)

    # (*) Pre Context State Machine
    #     (If present: All pre-context combined in single backward analyzer.)
    pre_context, reload_backward_state = \
                        generator.do_pre_context(g.pre_context_sm, 
                                                 g.pre_context_sm_id_list)

    # assert all_isinstance(pre_context, (IfDoorIdReferencedCode, int, str, unicode))
        
    # (*) Backward input position detection
    #     (Seldomly present -- only for Pseudo-Ambiguous Post Contexts)
    bipd, bipd_entry_door_id_db = generator.do_backward_input_position_detectors(g.bipd_sm_db)
    # assert all_isinstance(bipd, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Main State Machine -- try to match core patterns
    #     Post-context handling is webbed into the main state machine.
    main, reload_forward_state  = generator.do_main(g.sm, bipd_entry_door_id_db)
    # assert all_isinstance(main, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Reload procedures
    reload_procedures = generator.do_reload_procedures(reload_forward_state, reload_backward_state)
    # assert all_isinstance(reload_procedures, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Terminals
    terminals = generator.do_terminals(TerminalDb)

    # (*) Re-entry preparation
    reentry_prerpation = generator.do_reentry_preparation(g.pre_context_sm_id_list,
                                                          TerminalDb)

    # (*) State Router
    #     (Something that can goto a state address by an given integer value)
    state_router = generator.do_state_router()
    # assert all_isinstance(state_router, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Variable Definitions
    #     (Code that defines all required variables for the analyzer)
    variable_definitions = generator.do_variable_definitions()
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

    # (*) Make the analyzer function
    result = wrap_up(ModeName, function_body, variable_definitions, ModeNameList, 
                     AfterMatchF = (E_IncidenceIDs.AFTER_MATCH in IncidenceDb))

    return result, g.default_character_counter_required_f

def wrap_up(ModeName, FunctionBody, VariableDefs, ModeNameList, AfterMatchF):
    LanguageDB   = Setup.language_db
    txt_function = LanguageDB["$analyzer-func"](ModeName, Setup, VariableDefs, 
                                                FunctionBody, ModeNameList) 
    txt_header   = LanguageDB.HEADER_DEFINITIONS(AfterMatchF) 
    assert all_isinstance(txt_header, (str, unicode))

    txt_analyzer = get_plain_strings(txt_function)
    assert all_isinstance(txt_analyzer, (str, unicode))

    return txt_header + txt_analyzer

def do_default_counter(Mode):
    dial_db.clear()
    variable_db.init()

    default_character_counter_function_name,   \
    default_character_counter_function_code  = counter.get(Mode.counter_db, Mode.name)

    txt = "#ifdef      __QUEX_COUNT_VOID\n"                             \
          "#   undef   __QUEX_COUNT_VOID\n"                             \
          "#endif\n"                                                    \
          "#ifdef      __QUEX_OPTION_COUNTER\n"                         \
          "#    define __QUEX_COUNT_VOID(ME, BEGIN, END) \\\n"          \
          "            do {                              \\\n"          \
          "                %s((ME), (BEGIN), (END));     \\\n"          \
          "                __quex_debug_counter();       \\\n"          \
          "            } while(0)\n"                                    \
          "#else\n"                                                     \
          "#    define __QUEX_COUNT_VOID(ME, BEGIN, END) /* empty */\n" \
          "#endif\n"                                                    \
          % default_character_counter_function_name

    if default_character_counter_function_code is not None:
        txt += default_character_counter_function_code

    return txt

def frame_this(Code):
    return Setup.language_db["$frame"](Code, Setup)


