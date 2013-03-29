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
                                                          E_ActionIDs, \
                                                          setup as Setup

def do_mode(Mode, ModeNameList, IndentationSupportF, BeginOfLineSupportF):

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
    pattern_action_pair_list = action_preparation.do(Mode, 
                                                     IndentationSupportF, 
                                                     BeginOfLineSupportF)

    core_txt   = do(pattern_action_pair_list, 
                    FunctionPrefix = Mode.name, 
                    ModeNameList   = ModeNameList)

    # (*) Generate the counter first!
    #     (It may implement a state machine with labels and addresses
    #      which are not relevant for the main analyzer function.)
    counter_txt = do_counter(Mode)

    return counter_txt + core_txt

def do(PatternActionPair_List, FunctionPrefix=None, ModeNameList=None):
    """FunctionPrefix != None => A whole function is generated.
       else                   => Only a function body is produced.
    """
    generator = Generator(PatternActionPair_List) 

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
    function_body = []
    function_body.extend(pre_context)  # implementation of pre-contexts (if there are some)
    function_body.extend(main)         # main pattern matcher
    function_body.extend(bipd)         # (seldom != empty; only for pseudo-ambiguous post contexts)
    function_body.extend(state_router) # route to state by index (only if no computed gotos)
    if FunctionPrefix is not None:
        result = Generator.code_function(generator.action_db, 
                                         FunctionPrefix, 
                                         function_body,
                                         variable_definitions, 
                                         ModeNameList)
        return "".join(result)
    else:
        return function_body, variable_definitions

def do_counter(Mode):
    init_address_handling()
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

    def code_main_state_machine(self):
        LanguageDB    = Setup.language_db 
        txt, analyzer = Generator.code_state_machine(self.sm, engine.FORWARD)

        txt.extend(Generator.code_terminals(self.action_db, self.pre_context_sm_id_list))

        # Number of different entries in the position register map
        self.__position_register_n                 = len(set(analyzer.position_register_map.itervalues()))
        self.__last_acceptance_variable_required_f = analyzer.last_acceptance_variable_required()

        # -- reload definition (forward, backward, init state reload)
        txt.extend(LanguageDB.RELOAD())

        return txt

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
    def code_state_machine(sm, EngineType): 
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
        state_machine_code = state_machine_coder.do(analyzer)
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


