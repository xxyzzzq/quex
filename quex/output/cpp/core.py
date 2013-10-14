from   quex.engine.generator.languages.variable_db import variable_db
from   quex.engine.analyzer.door_id_address_label  import dial_db, IfDoorIdReferencedCode
from   quex.engine.generator.base                  import Generator as CppGenerator
from   quex.engine.tools                           import all_isinstance
import quex.output.cpp.action_preparation          as     action_preparation
import quex.output.cpp.counter                     as     counter
from   quex.blackboard                             import setup as Setup, \
                                                          E_ActionIDs

def do_mode(Mode, ModeNameList, IndentationSupportF, BeginOfLineSupportF):

    # (*) Initialize address handling
    #     (Must happen before call to constructor of Generator, because 
    #      constructor creates some addresses.)
    dial_db.clear()
    variable_db.init()

    # (*) Skippers, Indentation Handlers, etc. are generated in the 
    #     frame of 'action_preparation'. In there, somewhere, a call to
    #     'get_code()' happens. During parsing a 'GeneratedCode' object
    #     has been generated. When its 'get_code()' function is called,
    #     the skipper/indentation counter generation function is called.
    pattern_action_pair_list = action_preparation.do(Mode, 
                                                     IndentationSupportF, 
                                                     BeginOfLineSupportF)
    core_txt = do(pattern_action_pair_list, 
                  FunctionPrefix = Mode.name, 
                  ModeNameList   = ModeNameList)

    # (*) Generate the counter first!
    #     (It may implement a state machine with labels and addresses
    #      which are not relevant for the main analyzer function.)
    counter_txt = do_counter(Mode)

    return counter_txt + core_txt

def do(PatternActionPair_List, FunctionPrefix, ModeNameList):
    function_body,        \
    variable_definitions, \
    on_after_match_f      = do_core(PatternActionPair_List)

    result = CppGenerator.code_function(on_after_match_f, 
                                        FunctionPrefix, 
                                        function_body,
                                        variable_definitions, 
                                        ModeNameList)
    return "".join(result)

def do_core(PatternActionPair_List):
    """The initialization of addresses and variables is done outside 
       this function, since other components may influence it for the
       construction of a mode.
    """
    generator = CppGenerator(PatternActionPair_List) 

    # (*) Pre Context State Machine
    #     (If present: All pre-context combined in single backward analyzer.)
    pre_context          = generator.code_pre_context_state_machine()
    # assert all_isinstance(pre_context, (IfDoorIdReferencedCode, int, str, unicode))
        
    # (*) Backward input position detection
    #     (Seldomly present -- only for Pseudo-Ambiguous Post Contexts)
    bipd, bipd_entry_door_id_db = generator.code_backward_input_position_detection()
    # assert all_isinstance(bipd, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Main State Machine -- try to match core patterns
    #     Post-context handling is webbed into the main state machine.
    main                 = generator.code_main_state_machine(bipd_entry_door_id_db)
    # assert all_isinstance(main, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Reload procedures
    reload_procedures    = generator.code_reload_procedures()
    # assert all_isinstance(reload_procedures, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) State Router
    #     (Something that can goto a state address by an given integer value)
    state_router         = generator.state_router()
    # assert all_isinstance(state_router, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Variable Definitions
    #     (Code that defines all required variables for the analyzer)
    variable_definitions = generator.variable_definitions()
    # assert all_isinstance(variable_definitions, (IfDoorIdReferencedCode, int, str, unicode))

    # (*) Putting it all together
    function_body = []
    function_body.extend(pre_context)  # implementation of pre-contexts (if there are some)
    function_body.extend(main)         # main pattern matcher
    function_body.extend(bipd)         # (seldom != empty; only for pseudo-ambiguous post contexts)
    function_body.extend(state_router) # route to state by index (only if no computed gotos)
    function_body.extend(reload_procedures)

    return function_body, variable_definitions, generator.on_after_match_f

def do_counter(Mode):
    dial_db.clear()
    variable_db.init()

    if not Mode.default_character_counter_required_f():
        return ""

    default_character_counter_function_name,   \
    default_character_counter_function_code  = \
        counter.get(Mode.counter_db, Mode.name)

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


