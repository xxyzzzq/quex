import quex.engine.generator.languages.core            as     languages
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.languages.address         import get_label, get_address, \
                                                              get_label_of_address, \
                                                              get_plain_strings, \
                                                              init_address_handling, \
                                                              get_address_set_subject_to_routing, \
                                                              is_label_referenced

import quex.engine.generator.state_machine_coder       as     state_machine_coder
from   quex.engine.generator.state_machine_decorator   import StateMachineDecorator
import quex.engine.generator.state_router              as     state_router_generator
from   quex.engine.misc.string_handling                import blue_print
from   quex.engine.generator.base                      import GeneratorBase

from   quex.input.setup                                import setup as Setup
#
from   copy import copy

class Generator(GeneratorBase):

    def __init__(self, PatternActionPair_List, 
                 StateMachineName, 
                 OnFailureAction, EndOfStreamAction, 
                 ModeNameList, 
                 SupportBeginOfLineF):

        # Ensure that the language database as been setup propperly
        assert type(Setup.language_db) == dict
        assert len(Setup.language_db) != 0
        assert Setup.language_db.has_key("$label")

        self.state_machine_name         = StateMachineName
        self.language_db                = Setup.language_db
        self.end_of_stream_action       = EndOfStreamAction
        self.on_failure_action          = OnFailureAction
        self.mode_name_list             = ModeNameList

        GeneratorBase.__init__(self, PatternActionPair_List, StateMachineName, SupportBeginOfLineF)

    def do(self, RequiredLocalVariablesDB):
        LanguageDB = Setup.language_db

        dsm = StateMachineDecorator(self.sm, 
                                    self.state_machine_name, 
                                    self.post_contexted_sm_id_list, 
                                    BackwardLexingF=False, 
                                    BackwardInputPositionDetectionF=False)

        # (*) Initialize the label and variable trackers
        variable_db.init(RequiredLocalVariablesDB)
        init_address_handling(dsm.get_direct_transition_to_terminal_db())

        # (*) Pre Context State Machine
        #     (If present: All pre-context combined in single backward analyzer.)
        pre_context = self.__code_pre_context_state_machine()
            
        # (*) Main State Machine -- try to match core patterns
        main        = self.__code_main_state_machine(dsm)

        # (*) Backward input position detection
        #     (Seldomly present -- only for Pseudo-Ambiguous Post Contexts)
        bipd        = self.__code_backward_input_position_detection()

        # (*) Determine required labels and variables
        routed_address_set = get_address_set_subject_to_routing()

        state_router = []
        if len(routed_address_set) != 0 or is_label_referenced("$state-router"):
            variable_db.require("target_state_index", Condition_ComputedGoto=False) 

            routed_state_info_list = state_router_generator.get_info(routed_address_set, dsm)
            state_router.append(state_router_generator.do(routed_state_info_list))

        if is_label_referenced("$reload-FORWARD") or is_label_referenced("$reload-BACKWARD"):
            variable_db.require("target_state_else_index")
            variable_db.require("target_state_index")

        # Following function refers to the global 'variable_db'
        variable_definitions = self.language_db["$variable-definitions"](self.post_contexted_sm_id_list,
                                                                         self.pre_context_sm_id_list, 
                                                                         self.language_db)

        function_body = []
        function_body.extend(pre_context)  # implementation of pre-contexts (if there are some)
        function_body.extend(main)         # main pattern matcher
        function_body.extend(bipd)         # (seldom != empty; only for pseudo-ambiguous post contexts)
        function_body.extend(state_router) # route to state by index (only if no computed gotos)

        # (*) Pack Pre-Context and Core State Machine into a single function
        analyzer_function = self.language_db["$analyzer-func"](self.state_machine_name, 
                                                               Setup.analyzer_class_name,
                                                               Setup.single_mode_analyzer_f,
                                                               variable_definitions, 
                                                               function_body, 
                                                               self.mode_name_list, 
                                                               LanguageDB=self.language_db)

        txt  = [ LanguageDB["$header-definitions"](LanguageDB) ]
        txt += get_plain_strings(analyzer_function)
        return txt

    def __code_pre_context_state_machine(self):
        LanguageDB = self.language_db

        if len(self.pre_context_sm_list) == 0: return []

        assert len(self.pre_context_sm.get_orphaned_state_index_list()) == 0

        dsm = StateMachineDecorator(self.pre_context_sm, 
                                    self.state_machine_name, 
                                    PostContextSM_ID_List=[],
                                    BackwardLexingF=True, 
                                    BackwardInputPositionDetectionF=False)

        txt = []
        if Setup.comment_state_machine_transitions_f:
            comment = LanguageDB["$ml-comment"]("BEGIN: PRE-CONTEXT STATE MACHINE\n"             + \
                                                self.pre_context_sm.get_string(NormalizeF=False) + \
                                                "END: PRE-CONTEXT STATE MACHINE") 
            txt.append(comment)
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        msg = state_machine_coder.do(dsm)
        txt.extend(msg)

        txt.append(get_label("$terminal-general-bw") + ":\n")
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyzer went backwards, so it needs to be reset.
        txt.append("    QUEX_NAME(Buffer_seek_lexeme_start)(&me->buffer);\n")

        return txt

    def __code_main_state_machine(self, DSM):
        assert len(self.sm.get_orphaned_state_index_list()) == 0

        LanguageDB = self.language_db 
        txt        = []

        # -- [optional] comment state machine transitions 
        if Setup.comment_state_machine_transitions_f:
            comment = LanguageDB["$ml-comment"]("BEGIN: STATE MACHINE\n"             + \
                                                self.sm.get_string(NormalizeF=False) + \
                                                "END: STATE MACHINE") 
            txt.append(comment)
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        # -- implement the state machine itself
        state_machine_code = state_machine_coder.do(DSM)
        txt.extend(state_machine_code)

        # -- terminal states: execution of pattern actions  
        terminal_code = LanguageDB["$terminal-code"](DSM,
                                                     self.action_db, 
                                                     self.on_failure_action, 
                                                     self.end_of_stream_action, 
                                                     self.begin_of_line_condition_f, 
                                                     self.pre_context_sm_id_list,
                                                     self.language_db) 
        txt.extend(terminal_code)

        # -- reload definition (forward, backward, init state reload)
        code = LanguageDB["$reload-definitions"](self.sm.init_state_index)
        txt.extend(code)

        return txt

    def __code_backward_input_position_detection(self):
        result = []
        for sm in self.papc_backward_detector_state_machine_list:
            result.extend(self.__code_backward_input_position_detection_core(sm))
        return result

    def __code_backward_input_position_detection_core(self, sm):
        assert len(sm.get_orphaned_state_index_list()) == 0
        
        BIPD_ID = sm.get_id()

        dsm = StateMachineDecorator(sm, 
                                    "BACKWARD_DETECTOR_" + repr(sm.get_id()),
                                    PostContextSM_ID_List           = [], 
                                    BackwardLexingF                 = True, 
                                    BackwardInputPositionDetectionF = True)

        function_body = state_machine_coder.do(dsm)

        comment = []
        if Setup.comment_state_machine_transitions_f: 
            comment = Setup.language_db["$ml-comment"]("BEGIN: BACKWARD DETECTOR STATE MACHINE\n" + \
                                                       sm.get_string(NormalizeF=False)            + \
                                                       "\nEND: BACKWARD DETECTOR STATE MACHINE")
            comment.append("\n")


        # -- input position detectors: find first 'match' and return
        terminal = []
        terminal.append("\n")
        terminal.append("    __quex_assert_no_passage();\n")
        terminal.append(get_label("$bipd-terminal", BIPD_ID) + ":\n")
        terminal.append('    __quex_assert("backward input position %i detected");' % BIPD_ID)
        terminal.append("    " + self.language_db["$input/seek_position"]("end_of_core_pattern_position") + "\n")
        terminal.append("    " + self.language_db["$input/increment"] + "\n")
        terminal.append("    goto %s;\n" % get_label("$bipd-return", BIPD_ID, U=True))

        # Put all things together
        txt = []
        txt.append("    __quex_assert_no_passage();\n")
        txt.extend(comment)
        txt.extend(function_body)
        txt.extend(terminal)

        variable_db.require("end_of_core_pattern_position")

        return txt

def frame_this(Code):
    return Setup.language_db["$frame"](Code, Setup)

