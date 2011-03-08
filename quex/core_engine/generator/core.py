import quex.core_engine.generator.languages.core                   as     languages
from   quex.core_engine.generator.languages.address                import get_label, get_address, \
                                                                          get_plain_strings,      \
                                                                          find_routed_address_set
import quex.core_engine.generator.state_machine_coder              as     state_machine_coder
import quex.core_engine.generator.backward_input_position_detector_function as backward_detector_function
import quex.core_engine.generator.analyzer_function                         as analyzer_function
from   quex.core_engine.generator.state_machine_decorator          import StateMachineDecorator
import quex.core_engine.generator.state_router                     as     state_router
from   quex.input.setup                                            import setup as Setup
from   quex.frs_py.string_handling                                 import blue_print
from   copy                                                        import copy
#
from   quex.core_engine.generator.base                             import GeneratorBase

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

        # (*) Backward Input Position Detectors 
        #     If they are required (for pseudo ambiguous post conditions), then paste
        #     the **before** the regular analyzer function.
        for sm in self.papc_backward_detector_state_machine_list:
            txt.extend(self.backward_detector_function_get(sm))
        
        # (*) Main analyzer function
        txt.extend(self.analyzer_function_get())

        return txt

    def backward_detector_function_get(self, sm):
        prolog = """
        #include <quex/code_base/temporary_macros_on>
        QUEX_INLINE void 
        PAPC_input_postion_backward_detector_$$ID$$(QUEX_TYPE_ANALYZER* me) 
        {
        $$LOCAL_VARIABLES$$
        """

        epilog = """
        }
        #include <quex/code_base/temporary_macros_off>
        """
        assert sm.get_orphaned_state_index_list() == []

        dsm = StateMachineDecorator(sm, 
                                                        "BACKWARD_DETECTOR_" + repr(sm.get_id()),
                                                        PostContextSM_ID_List = [], 
                                                        BackwardLexingF=True, 
                                                        BackwardInputPositionDetectionF=True)

        function_body, variable_db, routed_address_set = state_machine_coder.do(dsm)

        if Setup.comment_state_machine_transitions_f: 
            comment = Setup.language_db["$ml-comment"]("BEGIN: BACKWARD DETECTOR STATE MACHINE\n" + \
                                                       sm.get_string(NormalizeF=False)            + \
                                                       "\nEND: BACKWARD DETECTOR STATE MACHINE")
            function_body.append(comment)
            fnuction_body.append("\n")


        # -- input position detectors simply the next 'catch' and return
        function_body.append("\n")
        function_body.append("    __quex_assert_no_passage();\n")
        function_body.append(self.language_db["$label-def"]("$terminal-general-bw") + "\n")
        function_body.append("    " + self.language_db["$input/seek_position"]("end_of_core_pattern_position") + "\n")
        function_body.append("    " + self.language_db["$input/increment"])

        txt, new_routed_address_set = get_plain_strings(function_body)
        routed_address_set.update(new_routed_address_set)

        if len(routed_address_set) != 0:
            function_body.extend(state_router.do(routed_address_set))
            variable_db["! QUEX_OPTION_COMPUTED_GOTOS/target_state_index"] = \
                         ["QUEX_TYPE_GOTO_LABEL", "(QUEX_TYPE_CHARACTER)(0x00)"]

        variable_db.update({
             "input":                        ["QUEX_TYPE_CHARACTER",          "(QUEX_TYPE_CHARACTER)(0x0)"],
             "end_of_core_pattern_position": ["QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER*)(0x0)"],
        })

        variables_txt = self.language_db["$local-variable-defs"](variable_db)

        txt = [ blue_print(prolog, 
                          [["$$ID$$",              repr(sm.get_id()).replace("L", "")],
                           ["$$LOCAL_VARIABLES$$", variables_txt],
                          ]) 
              ]
        txt.extend(function_body)

        txt.append(epilog)
            
        return txt

    def analyzer_function_get():
        routed_address_set = set([])
        local_variable_db  = copy(RequiredLocalVariablesDB)
        function_body      = []

        # (*) Pre Context State Machine
        #     All pre-context combined in single backward analyzer.
        if self.pre_context_sm_list != []:
            code, variable_db, new_routed_address_set = __backward_analyzer()

            local_variable_db.update(variable_db)
            function_body.extend(code)
            routed_address_set.update(new_routed_address_set)
            
        # (*) Core State Machine
        #     All pattern detectors combined in single forward analyzer
        code, variable_db, new_routed_address_set = self.__forward_analyzer()

        local_variable_db.update(variable_db)
        function_body.extend(code)
        routed_address_set.update(new_routed_address_set)

        if len(routed_address_set) != 0:
            routed_state_info_list = state_router.get_info(routed_address_set)
            function_body.extend(state_router.do(routed_state_info_list))

        # (*) Pack Pre-Context and Core State Machine into a single function
        analyzer_function = LanguageDB["$analyzer-func"](self.state_machine_name, 
                                                         self.analyzer_state_class_name, 
                                                         self.stand_alone_analyzer_f,
                                                         function_body, 
                                                         self.post_contexted_sm_id_list, 
                                                         self.pre_context_sm_id_list,
                                                         self.mode_name_list, 
                                                         InitialStateIndex=self.sm.init_state_index,
                                                         LanguageDB=LanguageDB,
                                                         LocalVariableDB=local_variable_db) 

        txt.extend(get_plain_strings(analyzer_function))

    def __backward_analyzer(self):
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

        msg, variable_db, routed_state_list = state_machine_coder.do(dsm)

        txt.extend(msg)

        txt.append(get_label("$terminal-general-bw") + ":\n")
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyzer went backwards, so it needs to be reset.
        txt.append("    QUEX_NAME(Buffer_seek_lexeme_start)(&me->buffer);\n")

        return txt, variable_db, routed_state_list

    def __forward_analyzer(self):
        LanguageDB = self.language_db 

        txt         = []
        variable_db = {}

        assert self.sm.get_orphaned_state_index_list() == []

        dsm = StateMachineDecorator(self.sm, 
                                    self.state_machine_name, 
                                    self.post_contexted_sm_id_list, 
                                    BackwardLexingF=False, 
                                    BackwardInputPositionDetectionF=False)

        # -- [optional] comment state machine transitions 
        if Setup.comment_state_machine_transitions_f:
            comment = LanguageDB["$ml-comment"]("BEGIN: STATE MACHINE\n"             + \
                                                self.sm.get_string(NormalizeF=False) + \
                                                "END: STATE MACHINE") 
            txt.append(comment)
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        # -- implement the state machine itself
        state_machine_code, db, routed_address_set = \
                state_machine_coder.do(dsm)

        variable_db.update(db)
        txt.extend(state_machine_code)

        # -- terminal states: execution of pattern actions  
        terminal_code, db = LanguageDB["$terminal-code"](dsm,
                                                         self.action_db, 
                                                         self.on_failure_action, 
                                                         self.end_of_stream_action, 
                                                         self.begin_of_line_condition_f, 
                                                         self.pre_context_sm_id_list,
                                                         self.language_db) 
        variable_db.update(db)
        txt.extend(terminal_code)

        # -- reload definition (forward, backward, init state reload)
        code = LanguageDB["$reload-definitions"](self.sm.init_state_index)
        txt.extend(code)

        routed_address_set.update(find_routed_address_set(txt))

        return txt, variable_db, routed_address_set


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

