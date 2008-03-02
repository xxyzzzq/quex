import quex.core_engine.generator.languages.core      as languages
import quex.core_engine.generator.languages.label     as languages_label
import quex.core_engine.generator.state_machine_coder as state_machine_coder
import quex.core_engine.generator.input_position_backward_detector     as backward_detector
import quex.core_engine.generator.combined_pre_condition_state_machine as combined_pre_condition_state_machine
#
from quex.core_engine.generator.base import GeneratorBase

class Generator(GeneratorBase):

    def __init__(self, PatternActionPair_List, 
                 StateMachineName, AnalyserStateClassName, Language, 
                 DefaultAction, QuexEngineHeaderDefinitionFile, ModeNameList, 
                 PrintStateMachineF, StandAloneAnalyserF,
                 ControlCharacterCodeList=[]):

        if not StandAloneAnalyserF: 
            assert QuexEngineHeaderDefinitionFile != "", \
               "Non-Stand-Alone Lexical Analyser cannot be created without naming explicitly\n" + \
               "a header file for the core engine define statements. See file\n" + \
               "$QUEX_DIR/code_base/core_engine/definitions-plain-memory.h for an example"       

        if QuexEngineHeaderDefinitionFile == "":
            QuexEngineHeaderDefinitionFile = "core_engine/definitions-plain-memory.h" 
    
        self.state_machine_name                  = StateMachineName
        self.analyzer_state_class_name           = AnalyserStateClassName
        self.programming_language                = Language
        self.language_db                         = languages.db[self.programming_language]
        self.default_action                      = DefaultAction
        self.core_engine_header_definitions_file = QuexEngineHeaderDefinitionFile
        self.mode_name_list                      = ModeNameList
        self.print_state_machine_f               = PrintStateMachineF
        self.stand_alone_analyzer_f              = StandAloneAnalyserF

        GeneratorBase.__init__(self, PatternActionPair_List, StateMachineName, ControlCharacterCodeList)

    def __get_core_state_machine(self):
        LanguageDB = self.language_db 

        #  -- comment all state machine transitions 
        txt = "    $/* state machine $*/\n"
        if self.print_state_machine_f: 
            txt += "    $/* " + repr(self.sm).replace("\n", "$*/\n    $/* ") + "\n"
        txt += state_machine_coder.do(self.sm, 
                                      LanguageDB                  = LanguageDB, 
                                      UserDefinedStateMachineName = self.state_machine_name, 
                                      BackwardLexingF             = False)

        
        #  -- terminal states: execution of pattern actions  
        txt += LanguageDB["$terminal-code"](self.state_machine_name, 
                                            self.sm, 
                                            self.action_db, 
                                            self.default_action, 
                                            self.begin_of_line_condition_f, 
                                            self.pre_condition_sm_id_list) 

        return txt

    def __get_combined_pre_condition_state_machine(self):
        LanguageDB = self.language_db

        txt = "    $/* state machine for pre-condition test: $*/\n"
        if self.print_state_machine_f: 
            txt += "    $/* " + repr(self.pre_condition_sm).replace("\n", "$*/\n    $/* ") + "$*/\n"

        txt += state_machine_coder.do(self.pre_condition_sm, 
                                      LanguageDB                  = LanguageDB, 
                                      UserDefinedStateMachineName = self.state_machine_name + "_PRE_CONDITION_",
                                      BackwardLexingF             = True)

        LabelName = languages_label.get_terminal(self.state_machine_name + "_PRE_CONDITION_")      
        txt += "%s\n" % LanguageDB["$label-definition"](LabelName) 
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyser went backwards, so it needs to be reset.
        txt += "    QUEX_CORE_SEEK_ANALYSER_START_POSITION;\n"

        return txt

    def do(self):

        LanguageDB = self.language_db

        #  -- state machines for backward input position detection (pseudo ambiguous post conditions)
        papc_input_postion_backward_detector_functions = ""
        for sm in self.papc_backward_detector_state_machine_list:
             papc_input_postion_backward_detector_functions +=  \
                  backward_detector.do(sm, LanguageDB, self.print_state_machine_f)
        function_body = ""
        # -- write the combined pre-condition state machine
        if self.pre_condition_sm_list != []:
            function_body += self.__get_combined_pre_condition_state_machine()
            
        # -- write the state machine of the 'core' patterns (i.e. no pre-conditions)
        function_body += self.__get_core_state_machine()

        # -- pack the whole thing into a function 
        analyzer_function = LanguageDB["$analyser-func"](self.state_machine_name, 
                                           self.analyzer_state_class_name, 
                                           self.stand_alone_analyzer_f,
                                           function_body, 
                                           self.post_conditioned_sm_id_list, self.pre_condition_sm_id_list,
                                           self.mode_name_list, 
                                           InitialStateIndex=self.sm.init_state_index) 

        option_str = ""
        if self.begin_of_line_condition_f: 
            option_str = LanguageDB["$compile-option"]("__QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION")

        #  -- paste the papc functions (if there are some) in front of the analyzer functions
        header_str = LanguageDB["$header-definitions"](self.core_engine_header_definitions_file)
        txt =   option_str                                     \
              + header_str                                     \
              + papc_input_postion_backward_detector_functions \
              + analyzer_function

        return languages.replace_keywords(txt, LanguageDB, NoIndentF=True)

def do(PatternActionPair_List, DefaultAction, Language="C++", StateMachineName="",
       PrintStateMachineF=False,
       AnalyserStateClassName="analyser_state",
       StandAloneAnalyserF=False,
       QuexEngineHeaderDefinitionFile="",
       ModeNameList=[],
       ControlCharacterCodeList=[]):
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
                     DefaultAction, QuexEngineHeaderDefinitionFile, ModeNameList, 
                     PrintStateMachineF, StandAloneAnalyserF, 
                     ControlCharacterCodeList).do()
    
