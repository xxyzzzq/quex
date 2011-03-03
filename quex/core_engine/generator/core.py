import quex.core_engine.generator.languages.core                   as     languages
from   quex.core_engine.generator.languages.core                   import Address, Reference
import quex.core_engine.generator.state_machine_coder              as     state_machine_coder
import quex.core_engine.generator.input_position_backward_detector as     backward_detector
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

    def __get_core_state_machine(self):
        LanguageDB = self.language_db 

        txt         = []
        variable_db = {}

        assert self.sm.get_orphaned_state_index_list() == []

        decorated_state_machine = StateMachineDecorator(self.sm, 
                                                        self.state_machine_name, 
                                                        self.post_contexted_sm_id_list, 
                                                        BackwardLexingF=False, 
                                                        BackwardInputPositionDetectionF=False)

        #  Comment state machine transitions 
        if Setup.comment_state_machine_transitions_f:
            comment = LanguageDB["$ml-comment"]("BEGIN: STATE MACHINE\n"             + \
                                                self.sm.get_string(NormalizeF=False) + \
                                                "END: STATE MACHINE") 
            txt.append(comment)
            txt.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

        state_machine_code, db, routed_state_info_list = state_machine_coder.do(decorated_state_machine)

        variable_db.update(db)
        txt.extend(state_machine_code)

        #  -- terminal states: execution of pattern actions  
        terminal_code, db = LanguageDB["$terminal-code"](decorated_state_machine,
                                                         self.action_db, 
                                                         self.on_failure_action, 
                                                         self.end_of_stream_action, 
                                                         self.begin_of_line_condition_f, 
                                                         self.pre_context_sm_id_list,
                                                         self.language_db) 
        variable_db.update(db)
        txt.extend(terminal_code)

        return txt, variable_db, routed_state_info_list

    def __get_combined_pre_context_state_machine(self):
        LanguageDB = self.language_db

        assert self.pre_context_sm.get_orphaned_state_index_list() == []

        decorated_state_machine = StateMachineDecorator(self.pre_context_sm, 
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

        msg, variable_db, routed_state_info_list = state_machine_coder.do(decorated_state_machine)

        txt.extend(msg)

        txt.append(LanguageDB["$label-def"]("$terminal-general-bw"))
        txt.append("\n")
        # -- set the input stream back to the real current position.
        #    during backward lexing the analyzer went backwards, so it needs to be reset.
        txt.append("    QUEX_NAME(Buffer_seek_lexeme_start)(&me->buffer);\n")

        return txt, variable_db, routed_state_info_list

    def do(self, RequiredLocalVariablesDB):
        function_body          = []
        local_variable_db      = copy(RequiredLocalVariablesDB)
        routed_state_info_list = []
        LanguageDB             = self.language_db

        txt = [ LanguageDB["$header-definitions"](LanguageDB) ]

        #  -- state machines for backward input position detection (pseudo ambiguous post conditions)
        #     paste the papc functions (if there are some) in front of the analyzer functions
        for sm in self.papc_backward_detector_state_machine_list:
            assert sm.get_orphaned_state_index_list() == []
            code = backward_detector.do(sm, LanguageDB)
            txt.extend(_get_propper_text(code))

        # -- write the combined pre-condition state machine
        if self.pre_context_sm_list != []:
            code,           \
            variable_db,    \
            state_info_list = self.__get_combined_pre_context_state_machine()

            local_variable_db.update(variable_db)
            function_body.extend(code)
            routed_state_info_list.extend(state_info_list)
            
        # -- write the state machine of the 'core' patterns (i.e. no pre-conditions)
        code,           \
        variable_db,    \
        state_info_list = self.__get_core_state_machine()

        local_variable_db.update(variable_db)
        function_body.extend(code)
        routed_state_info_list.extend(state_info_list)

        if len(routed_state_info_list) != 0:
            function_body.extend(state_router.do(routed_state_info_list))

        function_body = _get_propper_text(function_body)

        # -- pack the whole thing into a function 
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

        txt.append(analyzer_function)

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

def DELETED_init_unused_labels():
    ## print "##init,", languages.label_db_marker_get_unused_label_list()
    languages.label_db_marker_init()

def DELETED_delete_unused_labels(Code):
    """Delete unused labels, so that compilers won't complain.

       This function is performance critical, so we do a high speed replacement,
       where we write into the text itself. The original label is overwritten
       with the replaced label text.
       
       The body of this function contains the 'good old' but slow method
       in case that the new method has doubts about being able to perform well.
    """
    ## print "##delete,", languages.label_db_marker_get_unused_label_list()
    LanguageDB     = Setup.language_db
    replacement_db = {}
    code           = Code

    def fill_replacement_db(LabelList, format_func):
        for label in LabelList:
            original    = LanguageDB["$label-pure"](label)
            replacement = format_func(LanguageDB["$comment"](original))
            first_letter = original[0]
            if replacement_db.has_key(first_letter) == False:
                replacement_db[first_letter] = [ [original, replacement] ]
            else:
                replacement_db[first_letter].append([original, replacement])

    # Distinguish between:
    #   'nothing_labels'       -- labels that can be replaced by nothing.
    #   'computed_goto_labels' -- labels that must be replaced by conditional compilation
    nothing_label_list, computed_goto_label_list = languages.label_db_marker_get_unused_label_list()
    ## print "##nl", nothing_label_list
    ## print "##gl", computed_goto_label_list

    # (1) Replace labels that are not used at all.
    result = delete_unused_labels_FAST(code, nothing_label_list)
    if result == "": 
        # -- Fast replacement failed, add them to replacement db
        fill_replacement_db(nothing_label_list, lambda x: x)
    else:
        code = result

    # (2) Replace labels that only appear in computed gotos
    fill_replacement_db(computed_goto_label_list, 
                        lambda x: "#ifdef QUEX_OPTION_COMPUTED_GOTOS\n" + x + "#endif\n")
    
    for first_letter, replacement_list in replacement_db.items():
        code = blue_print(code, replacement_list, first_letter)

    return code
        
import array
def DELETED_delete_unused_labels_FAST(Code, LabelList):
    LanguageDB = Setup.language_db

    code = array.array("c", Code)
    if code.itemsize != 1: return ""

    comment_overhead = len(LanguageDB["$comment"](""))

    for label in LabelList:
        original = LanguageDB["$label-pure"](label)
        length = len(original)
        if length < 4: return ""
        idx = Code.find(original)
        # Replace label by spaces
        while idx != -1:
            i = idx
            while i < idx + length:
                code[i] = " "
                i += 1
            idx = Code.find(original, idx + length)

    return code.tostring()
        
_referenced_label_set = set([])
def _get_propper_text(txt_list):
    global referenced_label_set
    _referenced_label_set.clear()

    _referenced_label_set_search(txt_list)
    return _get_text(txt_list)

def _referenced_label_set_search(txt_list):
    global _referenced_label_set

    for i, elm in enumerate(txt_list):
        if isinstance(elm, Reference):
            _referenced_label_set.add(elm.label)
            # A reference has done its work as soon as it has notified about
            # its existence. Now, its code can replace its position.
            txt_list[i] = elm.code

        elif isinstance(elm, Address):
            # An 'addressed' code fragment may contain further references.
            _referenced_label_set_search(elm.code)
        
def _get_text(txt_list):
    """ -- If an addressed code fragment is referenced, then it is inserted.
        -- Integers are replaced by indentation, i.e. '1' = 4 spaces.
    """
    global _referenced_label_set

    for i, elm in enumerate(txt_list):
        if isinstance(elm, Address):
            if elm.label in _referenced_label_set: 
                txt_list[i] = _get_text(elm.code)
            else:
                txt_list[i] = ""          # not referenced -> not implemented

        elif type(elm) in [int, long]:    # Indentation: elm = number of indentations
            txt_list[i] = "    " * elm

    return "".join(txt_list)

