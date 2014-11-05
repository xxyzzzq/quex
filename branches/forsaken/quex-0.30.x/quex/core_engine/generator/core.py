import quex.core_engine.generator.languages.core      as languages
import quex.core_engine.generator.state_machine_coder as state_machine_coder
import quex.core_engine.generator.input_position_backward_detector   as backward_detector
from   quex.input.setup import setup as Setup
#
from quex.core_engine.generator.base import GeneratorBase

class Generator(GeneratorBase):

    def __init__(self, PatternActionPair_List, 
                 StateMachineName, AnalyserStateClassName, Language, 
                 DefaultAction, EndOfStreamAction, 
                 ModeNameList, 
                 PrintStateMachineF, StandAloneAnalyserF, EndOfFile_Code):

        self.state_machine_name                  = StateMachineName
        self.analyzer_state_class_name           = AnalyserStateClassName
        self.programming_language                = Language
        self.language_db                         = Setup.language_db
        self.end_of_stream_action                = EndOfStreamAction
        self.default_action                      = DefaultAction
        self.mode_name_list                      = ModeNameList
        self.print_state_machine_f               = PrintStateMachineF
        self.stand_alone_analyzer_f              = StandAloneAnalyserF
        self.end_of_file_code                    = EndOfFile_Code

        GeneratorBase.__init__(self, PatternActionPair_List, StateMachineName)

    def __get_core_state_machine(self):
        LanguageDB = self.language_db 

        assert self.sm.get_orphaned_state_index_list() == []

        #  -- comment all state machine transitions 
        txt = "    " + LanguageDB["$comment"]("state machine") + "\n"
        if self.print_state_machine_f: 
            txt += LanguageDB["$ml-comment"](self.sm.get_string(NormalizeF=False)) + "\n"

        msg, directly_reached_terminal_id_list = \
                state_machine_coder.do(self.sm, 
                                       StateMachineName                = self.state_machine_name, 
                                       BackwardLexingF                 = False,
                                       BackwardInputPositionDetectionF = False,
                                       PostConditionID_List            = self.post_contexted_sm_id_list) 
        txt += msg

        
        #  -- terminal states: execution of pattern actions  
        txt += LanguageDB["$terminal-code"](self.state_machine_name, 
                                            self.sm, 
                                            self.action_db, 
                                            self.default_action, 
                                            self.end_of_stream_action, 
                                            self.begin_of_line_condition_f, 
                                            self.pre_context_sm_id_list,
                                            self.language_db,
                                            directly_reached_terminal_id_list) 

        return txt

    def __get_combined_pre_context_state_machine(self):
        LanguageDB = self.language_db

        assert self.pre_context_sm.get_orphaned_state_index_list() == []

        txt = "    " + LanguageDB["$comment"]("state machine for pre-condition test:") + "\n"
        if self.print_state_machine_f: 
            txt += LanguageDB["$ml-comment"](self.pre_context_sm.get_string(NormalizeF=False)) + "\n"

        msg, dummy = state_machine_coder.do(self.pre_context_sm, 
                                            StateMachineName = self.state_machine_name,
                                            BackwardLexingF                 = True,
                                            BackwardInputPositionDetectionF = False,
                                            PostConditionID_List            = [])
        txt += msg

        txt += LanguageDB["$label-def"]("$terminal-general", True) + "\n"
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyser went backwards, so it needs to be reset.
        txt += "    QuexBuffer_seek_lexeme_start(&me->buffer);\n"

        return txt

    def do(self):
        LanguageDB = self.language_db

        #  -- state machines for backward input position detection (pseudo ambiguous post conditions)
        papc_input_postion_backward_detector_functions = ""
        for sm in self.papc_backward_detector_state_machine_list:
            assert sm.get_orphaned_state_index_list() == []
            papc_input_postion_backward_detector_functions +=  \
                  backward_detector.do(sm, LanguageDB, self.print_state_machine_f)

        function_body = ""
        # -- write the combined pre-condition state machine
        if self.pre_context_sm_list != []:
            function_body += self.__get_combined_pre_context_state_machine()
            
        # -- write the state machine of the 'core' patterns (i.e. no pre-conditions)
        function_body += self.__get_core_state_machine()

        # -- pack the whole thing into a function 
        analyzer_function = LanguageDB["$analyser-func"](self.state_machine_name, 
                                                         self.analyzer_state_class_name, 
                                                         self.stand_alone_analyzer_f,
                                                         function_body, 
                                                         self.post_contexted_sm_id_list, 
                                                         self.pre_context_sm_id_list,
                                                         self.mode_name_list, 
                                                         InitialStateIndex=self.sm.init_state_index,
                                                         LanguageDB=LanguageDB) 

        option_str = ""
        if self.begin_of_line_condition_f: 
            option_str = LanguageDB["$compile-option"]("__QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION")

        #  -- paste the papc functions (if there are some) in front of the analyzer functions
        header_str = LanguageDB["$header-definitions"](LanguageDB)
        txt =   option_str                                     \
              + header_str                                     \
              + papc_input_postion_backward_detector_functions \
              + analyzer_function

        return languages.replace_keywords(txt, LanguageDB, NoIndentF=True)

def do(PatternActionPair_List, DefaultAction, 
       EndOfStreamAction="", Language="C++", StateMachineName="",
       PrintStateMachineF=False,
       AnalyserStateClassName="analyser_state",
       StandAloneAnalyserF=False,
       QuexEngineHeaderDefinitionFile="",
       ModeNameList=[],
       EndOfFile_Code=0):
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
                     DefaultAction, EndOfStreamAction, ModeNameList, 
                     PrintStateMachineF, StandAloneAnalyserF, EndOfFile_Code).do()
    
