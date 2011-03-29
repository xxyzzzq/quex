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
import quex.engine.generator.state_router              as     state_router
from   quex.engine.misc.string_handling                import blue_print
from   quex.engine.generator.base                      import GeneratorBase

from   quex.input.setup                                import setup as Setup
#
from   copy import copy

class Generator(GeneratorBase):

    def __init__(self, PatternActionPair_List, 
                 StateMachineName, AnalyserStateClassName, Language, 
                 OnFailureAction, EndOfStreamAction, 
                 ModeNameList, 
                 StandAloneAnalyserF, SupportBeginOfLineF):

        # Ensure that the language database as been setup propperly
        assert type(Setup.language_db) == dict
        assert len(Setup.language_db) != 0
        assert Setup.language_db.has_key("$label")

        self.state_machine_name         = StateMachineName
        self.analyzer_state_class_name  = AnalyserStateClassName
        self.programming_language       = Language
        self.language_db                = Setup.language_db
        self.end_of_stream_action       = EndOfStreamAction
        self.on_failure_action          = OnFailureAction
        self.mode_name_list             = ModeNameList
        self.stand_alone_analyzer_f     = StandAloneAnalyserF

        GeneratorBase.__init__(self, PatternActionPair_List, StateMachineName, SupportBeginOfLineF)

    def do(self, RequiredLocalVariablesDB):
        LanguageDB = self.language_db

        txt = [ LanguageDB["$header-definitions"](LanguageDB) ]

        # (*) Main analyzer function
        txt.extend(self.analyzer_function_get(RequiredLocalVariablesDB))

        return txt

    def backward_detector_function_get(self, sm):
        assert sm.get_orphaned_state_index_list() == []
        
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


        # -- input position detectors simply the next 'catch' and return
        terminal = []
        terminal.append("\n")
        terminal.append("    __quex_assert_no_passage();\n")
        terminal.append(get_label("$bipd-terminal", BIPD_ID) + ":\n")
        terminal.append('    __quex_assert("backward input position %i detected");' % BIPD_ID)
        terminal.append("    " + self.language_db["$input/seek_position"]("end_of_core_pattern_position") + "\n")
        terminal.append("    " + self.language_db["$input/increment"] + "\n")
        terminal.append("    goto %s;\n" % get_label("$bipd-return", BIPD_ID, U=True))

        routed_address_set = get_address_set_subject_to_routing()

        state_router_txt = ""
        if len(routed_address_set) != 0:
            routed_state_info_list = state_router.get_info(routed_address_set, dsm)
            state_router_txt       = state_router.do(routed_state_info_list)
            variable_db.require("target_state_index", Condition_ComputedGoto=False)

        # Put all things together
        txt = []
        txt.append("    __quex_assert_no_passage();\n")
        txt.append("%s:\n" % get_label("$bipd-entry", BIPD_ID))
        txt.append('    __quex_debug("backward input position detection %i");\n' % BIPD_ID)
        txt.extend(comment)
        txt.extend(function_body)
        txt.extend(terminal)

        variable_db.require("end_of_core_pattern_position")
        return get_plain_strings(txt)

    def analyzer_function_get(self, RequiredLocalVariablesDB):
        routed_address_set = set([])
        function_body      = []

        # (*) Core State Machine
        #     All pattern detectors combined in single forward analyzer
        dsm = StateMachineDecorator(self.sm, 
                                    self.state_machine_name, 
                                    self.post_contexted_sm_id_list, 
                                    BackwardLexingF=False, 
                                    BackwardInputPositionDetectionF=False)

        variable_db.init(RequiredLocalVariablesDB)
        init_address_handling(dsm.get_direct_transition_to_terminal_db())

        # (*) Pre Context State Machine
        #     All pre-context combined in single backward analyzer.
        if self.pre_context_sm_list != []:
            code = self.__pre_condition_state_coder()
            function_body.extend(code)
            
        # -- now, consider core state machine
        code = self.__forward_analyzer(dsm)
        function_body.extend(code)

        # At this point in time, the function body is completely defined
        routed_address_set = get_address_set_subject_to_routing()

        if len(routed_address_set) != 0 or is_label_referenced("$state-router"):
            routed_state_info_list = state_router.get_info(routed_address_set, dsm)
            function_body.append(state_router.do(routed_state_info_list))
            variable_db.require("target_state_index", Condition_ComputedGoto=False) 

        if is_label_referenced("$reload-FORWARD") or is_label_referenced("$reload-BACKWARD"):
            variable_db.require("target_state_else_index")
            variable_db.require("target_state_index")

        # Backward input position detection
        # (Pseudo-Ambigous Post Contexts)
        for sm in self.papc_backward_detector_state_machine_list:
            function_body.extend(self.backward_detector_function_get(sm))

        # Following function refers to the global 'variable_db'
        variable_definitions = self.language_db["$variable-definitions"](self.post_contexted_sm_id_list,
                                                                         self.pre_context_sm_id_list, 
                                                                         self.language_db)

        # (*) Pack Pre-Context and Core State Machine into a single function
        analyzer_function = self.language_db["$analyzer-func"](self.state_machine_name, 
                                                               self.analyzer_state_class_name, 
                                                               self.stand_alone_analyzer_f,
                                                               variable_definitions, 
                                                               function_body, 
                                                               self.mode_name_list, 
                                                               LanguageDB=self.language_db)

        return get_plain_strings(analyzer_function)

    def __pre_condition_state_coder(self):
        LanguageDB = self.language_db

        assert self.pre_context_sm.get_orphaned_state_index_list() == []

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

    def __forward_analyzer(self, DSM):
        assert self.sm.get_orphaned_state_index_list() == []

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

def do(PatternActionPair_List, OnFailureAction, 
       EndOfStreamAction, Language="C++", StateMachineName="",
       AnalyserStateClassName="analyzer_state",
       StandAloneAnalyserF=False,
       QuexEngineHeaderDefinitionFile="",
       ModeNameList=[],
       RequiredLocalVariablesDB={}, 
       SupportBeginOfLineF=False):
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
    return Generator(PatternActionPair_List, 
                     StateMachineName, AnalyserStateClassName, Language, 
                     OnFailureAction, EndOfStreamAction, ModeNameList, 
                     StandAloneAnalyserF, SupportBeginOfLineF).do(RequiredLocalVariablesDB)
    
def frame_this(Code):
    return Setup.language_db["$frame"](Code, Setup)

