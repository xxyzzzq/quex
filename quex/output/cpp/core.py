import quex.engine.analyzer.engine_supply_factory  as     engine
from   quex.engine.generator.languages.variable_db import variable_db
from   quex.engine.generator.languages.address     import get_address,                        \
                                                          get_plain_strings,                  \
                                                          init_address_handling,              \
                                                          get_address_set_subject_to_routing, \
                                                          is_label_referenced
import quex.engine.generator.state_machine_coder   as     state_machine_coder
import quex.engine.generator.state_router          as     state_router_generator
from   quex.engine.generator.base                  import GeneratorBase
import quex.engine.analyzer.core                   as     analyzer_generator
import quex.output.cpp.action_preparation          as     action_preparation
import quex.output.cpp.counter                     as     counter
from   quex.blackboard                             import E_StateIndices, \
                                                          setup as Setup

def do(Mode, ModeNameList, IndentationSupportF, BeginOfLineSupportF):

    # (*) Initialize address handling
    #     (Must happen before call to constructor of Generator, because 
    #      constructor creates some addresses.)
    init_address_handling()
    variable_db.init()

    # (*) Skippers, Indentation Handlers, etc. are generated in the 
    #     frame of 'action_preparation'. In there, somewhere, a call to
    #     'get_code()' happens. During parsing a 'GeneratedCode' object
    #     has been generated. When its 'get_code()' function is called,
    #     the skipper/indentation counter generation function is called.
    pattern_action_pair_list, \
    on_end_of_stream_action,  \
    on_failure_action,        \
    on_after_match            = action_preparation.do(Mode, 
                                                      IndentationSupportF, 
                                                      BeginOfLineSupportF)

    generator = Generator(Mode                   = Mode, 
                          PatternActionPair_List = pattern_action_pair_list, 
                          Action_OnEndOfStream   = on_end_of_stream_action, 
                          Action_OnFailure       = on_failure_action, 
                          Action_OnAfterMatch    = on_after_match, 
                          ModeNameList           = ModeNameList)

    return _counter(Mode) + _do(generator)

def _do(generator):
    # (*) Initialize the label and variable trackers
    variable_db.require("input") 

    # (*) Pre Context State Machine
    #     (If present: All pre-context combined in single backward analyzer.)
    pre_context          = generator.code_pre_context_state_machine()
        
    # (*) Main State Machine -- try to match core patterns
    #     Post-context handling is webbed into the main state machine.
    main                 = generator.code_main_state_machine()

    # (*) Backward input position detection
    #     (Seldomly present -- only for Pseudo-Ambiguous Post Contexts)
    bipd                 = generator.code_backward_input_position_detection()

    # (*) State Router
    #     (Something that can goto a state address by an given integer value)
    state_router         = generator.state_router()

    # (*) Variable Definitions
    #     (Code that defines all required variables for the analyzer)
    variable_definitions = generator.variable_definitions()

    # (*) Putting it all together
    result               = generator.analyzer_function(pre_context, main, bipd, 
                                                       state_router, 
                                                       variable_definitions)
    return "".join(result)

def _counter(Mode):
    if not Mode.default_character_counter_required_f():
        return 

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

class Generator(GeneratorBase):

    def __init__(self, Mode, PatternActionPair_List,
                 Action_OnEndOfStream, Action_OnFailure, Action_OnAfterMatch, ModeNameList): 

        # Ensure that the language database as been setup propperly
        assert isinstance(Setup.language_db, dict)
        assert len(Setup.language_db) != 0

        # -- prepare the source code fragments for the generator
        self.on_end_of_stream_action = Action_OnEndOfStream
        self.on_failure_action       = Action_OnFailure
        self.on_after_match          = Action_OnAfterMatch

        self.state_machine_name = Mode.name
        self.language_db        = Setup.language_db
        self.mode_name_list     = ModeNameList

        GeneratorBase.__init__(self, PatternActionPair_List, self.state_machine_name)

    def code_pre_context_state_machine(self):
        LanguageDB = self.language_db

        if len(self.pre_context_sm_list) == 0: return []

        assert len(self.pre_context_sm.get_orphaned_state_index_list()) == 0

        txt = []
        if Setup.comment_state_machine_f:
            LanguageDB.ML_COMMENT(txt, 
                                  "BEGIN: PRE-CONTEXT STATE MACHINE\n"             + \
                                  self.pre_context_sm.get_string(NormalizeF=False) + \
                                  "END: PRE-CONTEXT STATE MACHINE") 
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        analyzer = analyzer_generator.do(self.pre_context_sm, engine.BACKWARD_PRE_CONTEXT)
        LanguageDB.REPLACE_INDENT(analyzer)
        msg      = state_machine_coder.do(analyzer)
        txt.extend(msg)

        txt.append("\n%s" % LanguageDB.LABEL(E_StateIndices.END_OF_PRE_CONTEXT_CHECK))
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyzer went backwards, so it needs to be reset.
        txt.append("    %s\n" % LanguageDB.INPUT_P_TO_LEXEME_START())

        for sm_id in self.pre_context_sm_id_list:
            variable_db.require("pre_context_%i_fulfilled_f", Index = sm_id)

        return txt

    def code_main_state_machine(self):
        assert len(self.sm.get_orphaned_state_index_list()) == 0

        LanguageDB = self.language_db 
        txt        = []

        # -- [optional] comment state machine transitions 
        if Setup.comment_state_machine_f:
            LanguageDB.ML_COMMENT(txt, 
                                  "BEGIN: STATE MACHINE\n"             + \
                                  self.sm.get_string(NormalizeF=False) + \
                                  "END: STATE MACHINE") 
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        # -- implement the state machine itself
        analyzer           = analyzer_generator.do(self.sm, engine.FORWARD)
        state_machine_code = state_machine_coder.do(analyzer)
        LanguageDB.REPLACE_INDENT(state_machine_code)
        txt.extend(state_machine_code)

        # -- terminal states: execution of pattern actions  
        terminal_code = LanguageDB["$terminal-code"](self.state_machine_name,
                                                     self.action_db, 
                                                     variable_db,
                                                     self.pre_context_sm_id_list,
                                                     self.on_failure_action, 
                                                     self.on_end_of_stream_action, 
                                                     self.on_after_match, 
                                                     Setup) 
        
        txt.extend(terminal_code)

        N = len(set(analyzer.position_register_map.values()))
        if len(analyzer.position_register_map) == 0:
            variable_db.require("position",          Initial = "(void*)0x0", Type = "void*")
            variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % N)
        else:
            variable_db.require_array("position", ElementN = N,
                                      Initial  = "{ " + ("0, " * (N - 1) + "0") + "}")
            variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % N)
    
        if analyzer.last_acceptance_variable_required():
            variable_db.require("last_acceptance")

        # -- reload definition (forward, backward, init state reload)
        code = LanguageDB.RELOAD()
        txt.extend(code)

        return txt

    def code_backward_input_position_detection(self):
        result = []
        for sm in self.bipd_sm_list:
            result.extend(self.__code_backward_input_position_detection_core(sm))
        return result

    def __code_backward_input_position_detection_core(self, SM):
        assert len(SM.get_orphaned_state_index_list()) == 0
        
        txt = []
        if Setup.comment_state_machine_f: 
            self.language_db.ML_COMMENT(txt, 
                                         "BEGIN: BACKWARD DETECTOR STATE MACHINE\n" + \
                                         SM.get_string(NormalizeF=False)            + \
                                         "\nEND: BACKWARD DETECTOR STATE MACHINE")
            txt.append("\n")

        analyzer      = analyzer_generator.do(SM, engine.BACKWARD_INPUT_POSITION)
        function_body = state_machine_coder.do(analyzer)
        LanguageDB.REPLACE_INDENT(function_body)

        txt.extend(function_body)

        return txt

    def state_router(self):
        # (*) Determine required labels and variables
        routed_address_set = get_address_set_subject_to_routing()
        routed_address_set.add(get_address("$terminal-EOF", U=True))
        routed_state_info_list = state_router_generator.get_info(routed_address_set)
        return [ state_router_generator.do(routed_state_info_list) ]

    def variable_definitions(self):
        variable_db.require("target_state_index", Condition_ComputedGoto=False) 

        if is_label_referenced("$reload-FORWARD") or is_label_referenced("$reload-BACKWARD"):
            variable_db.require("target_state_else_index")
            variable_db.require("target_state_index")

        # Following function refers to the global 'variable_db'
        return self.language_db.VARIABLE_DEFINITIONS(variable_db)

    def analyzer_function(self, PreContext, Main, BIPD, StateRouter, VariableDefs):
        function_body = []
        function_body.extend(PreContext)  # implementation of pre-contexts (if there are some)
        function_body.extend(Main)        # main pattern matcher
        function_body.extend(BIPD)        # (seldom != empty; only for pseudo-ambiguous post contexts)
        function_body.extend(StateRouter) # route to state by index (only if no computed gotos)

        # (*) Pack Pre-Context and Core State Machine into a single function
        analyzer_function = self.language_db["$analyzer-func"](self.state_machine_name, 
                                                               Setup,
                                                               VariableDefs, 
                                                               function_body, 
                                                               self.mode_name_list) 

        txt  = [ self.language_db["$header-definitions"](self.language_db, self.on_after_match) ]
        txt += get_plain_strings(analyzer_function)

        Generator.assert_txt(txt)

        return txt

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

def frame_this(Code):
    return Setup.language_db["$frame"](Code, Setup)

