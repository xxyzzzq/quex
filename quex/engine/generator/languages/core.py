# PURPOSE: Providing a database for code generation in different programming languages.
#          A central object 'db' contains for each keyword, such as '$if' '$else' a correspondent
#          keyword or sequence that corresponds to it in the given language. Some code
#          elements are slighly more complicated. Therefore the db returns for some keywords
#          a function that generates the correspondent code fragment.
# 
# NOTE: The language of reference is C++. At the current state the python code generation 
#       is only suited for unit test of state transitions, no state machine code generation.
#       Basics for other languages are in place (VisualBasic, Perl, ...) but no action has been
#       taken to seriously implement them.
#
# AUTHOR: Frank-Rene Schaefer
# ABSOLUTELY NO WARRANTY
#########################################################################################################
import quex.engine.generator.languages.cpp       as     cpp
from   quex.engine.generator.languages.address   import get_address, \
                                                        db, \
                                                        get_label, \
                                                        Address
from   quex.blackboard                           import E_StateIndices,  \
                                                        E_EngineTypes,   \
                                                        E_AcceptanceIDs, \
                                                        E_InputActions,  \
                                                        E_TransitionN,   \
                                                        E_PreContextIDs
from   quex.engine.analyzer.state_entry          import Action_Accepter, \
                                                        Action_StoreInputPosition, \
                                                        Action_PreConditionOK
from   copy                                      import copy

from   itertools import islice

#________________________________________________________________________________
# C++
#    
CppBase = {
    "$class-member-def":   lambda TypeStr, MaxTypeNameL, VariableName, MaxVariableL:
                           "    %s%s %s;" % (TypeStr, " " * (MaxTypeNameL - len(TypeStr)), VariableName),
    "$require-terminating-zero-preparation": cpp.__require_terminating_zero_preparation,
    "$indentation_add":          cpp.__indentation_add,
    "$indentation_check_space":  cpp.__indentation_check_whitespace,
    #
    "$analyzer-func":           cpp.__analyzer_function,
    "$terminal-code":           cpp.__terminal_states,      
    "$header-definitions":      cpp.__header_definitions,
    "$frame":                   cpp.__frame_of_all,
    "$code_base":               "/quex/code_base/",
    "$token-default-file":      "/token/CppDefault.qx",
    "$token_template_file":     "/token/TXT-Cpp",
    "$token_template_i_file":   "/token/TXT-Cpp.i",
    "$analyzer_template_file":  "/analyzer/TXT-Cpp",
    "$file_extension":          ".cpp",
}

class LDB(dict):
    def __init__(self, DB):      
        self.update(DB)
        self.__analyzer = None

    def register_analyzer(self, TheAnalyzer):
        self.__analyzer = TheAnalyzer

    @property
    def analyzer(self):
        return self.__analyzer

    def __getattr__(self, Attr): 
        return self[Attr]

    RETURN                  = "return;"
    UNREACHABLE             = "__quex_assert_no_passage();"
    ELSE                    = "} else {\n"

    PATH_ITERATOR_INCREMENT = "++(path_iterator);"
    BUFFER_LIMIT_CODE       = "QUEX_SETTING_BUFFER_LIMIT_CODE"
    COMMENT_DELIMITERS      = [["/*", "*/", ""], ["//", "\n", ""], ["\"", "\"", "\\\""]]
    def LEXEME_START_SET(self, PositionStorage=None):
        if PositionStorage is None: return "me->buffer._lexeme_start_p = me->buffer._input_p;"
        else:                       return "me->buffer._lexeme_start_p = %s;" % PositionStorage
    def LEXEME_LENGTH(self):
        return "((size_t)(me->buffer._input_p - me->buffer._lexeme_start_p))"

    def INPUT_P(self):                 return "me->buffer._input_p"
    def INPUT_P_INCREMENT(self):       return "++(me->buffer._input_p);"
    def INPUT_P_DECREMENT(self):       return "--(me->buffer._input_p);"
    def INPUT_P_ADD(self, Offset):     return "QUEX_NAME(Buffer_input_p_add_offset)(&me->buffer, %i);" % Offset
    def INPUT_P_TO_LEXEME_START(self): return "me->buffer._input_p = me->buffer._lexeme_start_p;"
    def INPUT_P_DEREFERENCE(self, Offset=0): 
        if Offset == 0: return "*(me->buffer._input_p)"
        else:           return "QUEX_NAME(Buffer_input_get_offset)(&me->buffer, %i)" % Offset

    def NAMESPACE_OPEN(self, NameList):
        txt = ""
        i = -1
        for name in NameList:
            i += 1
            txt += "    " * i + "namespace %s {\n" % name
        return txt

    def NAMESPACE_CLOSE(self, NameList):
        txt = ""
        for name in NameList:
            txt += "} /* Closing Namespace '%s' */\n" % name
        return txt

    def NAMESPACE_REFERENCE(self, NameList):
        return reduce(lambda x, y: x + "::" + y, [""] + NameList) + "::"

    def COMMENT(self, txt, Comment):
        """Eliminated Comment Terminating character sequence from 'Comment'
           and comment it into a single line comment.
           For compatibility with C89, we use Slash-Star comments only, no '//'.
        """
        comment = Comment.replace("/*", "SLASH_STAR").replace("*/", "STAR_SLASH")
        txt.append("/* %s */\n" % comment)

    def ML_COMMENT(self, txt, Comment):
        comment = Comment.replace("/*", "SLASH_STAR").replace("*/", "STAR_SLASH").replace("\n", "\n     * ")
        txt.append("    /* %s\n     */" % comment) 

    def ACTION(self, EntryAction):
        if isinstance(EntryAction, Action_Accepter):
            else_str = ""
            txt      = []
            for element in EntryAction:
                if element.pre_context_id != E_PreContextIDs.NONE:
                    txt.append("    %sif( pre_context_%i_fulfilled_f ) last_acceptance = %s;\n" \
                               % (else_str, 
                                  element.pre_context_id, 
                                  self.ACCEPTANCE(element.pattern_id)))
                else:
                    txt.append("    %slast_acceptance = %s;\n" \
                               % (else_str, self.ACCEPTANCE(element.pattern_id)))
                else_str = "else "
            return "".join(txt)

        elif isinstance(EntryAction, Action_StoreInputPosition):
            # Assume that checking for the pre-context is just overhead that 
            # does not accelerate anything.
            if EntryAction.offset == 0:
                return "    position[%i] = me->buffer._input_p;\n" \
                       % EntryAction.position_register
            else:
                return "    position[%i] = me->buffer._input_p - %i;\n" \
                       % (EntryAction.position_register, EntryAction.offset)
        elif isinstance(EntryAction, Action_PreConditionOK):
            return "    pre_context_%i_fulfilled_f = 1;\n" % EntryAction.pre_context_id
        else:
            assert False, "Unknown Entry Action"

    def ADDRESS(self, StateIndex, FromStateIndex, DoorIndex=None):
        # The door can be specified by the FromStateIndex or the DoorIndex but not by both!
        assert not (FromStateIndex != None and DoorIndex != None)

        if DoorIndex is None:
            if self.__analyzer is None:
                DoorIndex = None

            elif self.__analyzer.engine_type == E_EngineTypes.BACKWARD_INPUT_POSITION:
                DoorIndex = None

            elif FromStateIndex is not None:
                if self.__analyzer.state_db.has_key(StateIndex) == False:
                    # It must be a template/path walker state. Those are not real analyzer states
                    # but little engines that can be entered via an address.
                    DoorIndex = None
                else:
                    DoorIndex = self.__analyzer.state_db[StateIndex].entry.source_state_to_group_db[FromStateIndex]
        elif DoorIndex == 0:
            # Door '0' is always the state itself
            DoorIndex = None

        result = get_address("$entry", (StateIndex, DoorIndex), U=True, R=True)
        return result

    def ADDRESS_DROP_OUT(self, StateIndex):
        return get_address("$drop-out", StateIndex)

    def __label_name(self, StateIndex, FromStateIndex=None, DoorIndex=None):
        assert type(DoorIndex) != bool
        if StateIndex in E_StateIndices:
            assert StateIndex != E_StateIndices.DROP_OUT
            assert StateIndex != E_StateIndices.RELOAD_PROCEDURE
            return {
                E_StateIndices.INIT_STATE_TRANSITION_BLOCK: "INIT_STATE_TRANSITION_BLOCK",
                E_StateIndices.END_OF_PRE_CONTEXT_CHECK:    "END_OF_PRE_CONTEXT_CHECK",
                E_StateIndices.ANALYZER_REENTRY:            "__REENTRY",
            }[StateIndex]

        return "_%i" % self.ADDRESS(StateIndex, FromStateIndex, DoorIndex)

    def LABEL(self, StateIndex, FromStateIndex=None, DoorIndex=None, NewlineF=True):
        assert type(DoorIndex) != bool
        label = self.__label_name(StateIndex, FromStateIndex, DoorIndex)
        if NewlineF: return label + ":\n"
        return label + ":"

    def LABEL_DROP_OUT(self, StateIndex):
        return "_%s:" % self.ADDRESS_DROP_OUT(StateIndex)

    def LABEL_INIT_STATE_TRANSITION_BLOCK(self):
        return "%s:\n" % self.__label_name(E_StateIndices.INIT_STATE_TRANSITION_BLOCK)

    def LABEL_SHARED_ENTRY(self, TemplateIndex, EntryN=None):
        if EntryN is None: return "_%i_shared_entry:\n"    % TemplateIndex
        else:              return "_%i_shared_entry_%i:\n" % (TemplateIndex, EntryN)

    def LABEL_NAME_BACKWARD_INPUT_POSITION_DETECTOR(self, StateMachineID):
        return "BIP_DETECTOR_%i" % StateMachineID

    def LABEL_NAME_BACKWARD_INPUT_POSITION_RETURN(self, StateMachineID):
        return "BIP_DETECTOR_%i_DONE" % StateMachineID

    def GOTO(self, TargetStateIndex, FromStateIndex=None, DoorIndex=None):
        # Only for normal 'forward analysis' the from state is of interest.
        # Because, only during forward analysis some actions depend on the 
        # state from where we come.
        result = "goto %s;" % self.__label_name(TargetStateIndex, FromStateIndex, DoorIndex)
        return result

    def GOTO_DROP_OUT(self, StateIndex):
        return "goto %s;" % get_label("$drop-out", StateIndex, U=True, R=True)

    def GOTO_RELOAD(self, StateIndex, InitStateIndexF, EngineType):
        """On reload a special section is entered that tries to reload data. Reload
           has two possible results:
           
           -- Data has been loaded: Now, a new input character can be determined
              and the current transition map can be reentered. For convenience, 
              'RELOAD' expects to jump to right before the place where the input
              pointer is adapted.

           -- No data available to be loaded: Then the current state's drop-out
              section must be entered. The forward init state immediate jumps
              to 'end of stream'.

           Thus: The reload behavior can be determined based on **one** state index.
                 The related drop-out label can be determined here.
        """
        direction = { 
            E_EngineTypes.FORWARD:              "FORWARD",
            E_EngineTypes.BACKWARD_PRE_CONTEXT: "BACKWARD",
            E_EngineTypes.BACKWARD_INPUT_POSITION: "",
            # There is never a reload on backward input position detection.
            # The lexeme to parse must lie inside the borders!
        }[EngineType]

        on_success = get_address("$entry", StateIndex, U=True)
        if InitStateIndexF and EngineType == E_EngineTypes.FORWARD:
            on_fail = get_address("$terminal-EOF", U=True) 
        else:
            on_fail = get_address("$drop-out", StateIndex, U=True, R=True) 

        get_label("$state-router", U=True)            # Mark as 'referenced'
        get_label("$reload-%s" % direction, U=True)   # ...
        return "QUEX_GOTO_RELOAD_%s(%s, %s);" % (direction, on_success, on_fail)

    def GOTO_TERMINAL(self, AcceptanceID):
        if AcceptanceID == E_AcceptanceIDs.VOID: 
            return "QUEX_GOTO_TERMINAL(last_acceptance);"
        elif AcceptanceID == E_AcceptanceIDs.FAILURE:
            return "goto _%i; /* TERMINAL_FAILURE */" % get_address("$terminal-FAILURE")
        else:
            assert isinstance(AcceptanceID, (int, long))
            return "goto TERMINAL_%i;" % AcceptanceID

    def GOTO_SHARED_ENTRY(self, TemplateIndex, EntryN=None):
        if EntryN is None: return "goto _%i_shared_entry;"    % TemplateIndex
        else:              return "goto _%i_shared_entry_%i;" % (TemplateIndex, EntryN)

    def MODE_GOTO(self, Mode):
        return "QUEX_NAME(enter_mode)(&self, &%s);" % Mode

    def MODE_GOSUB(self, Mode):
        return "QUEX_NAME(push_mode)(&self, &%s);" % Mode

    def MODE_GOUP(self):
        return "QUEX_NAME(pop_mode)(&self);"

    def ACCEPTANCE(self, AcceptanceID):
        if AcceptanceID == E_AcceptanceIDs.FAILURE: return "((QUEX_TYPE_ACCEPTANCE_ID)-1)"
        else:                                       return "%i" % AcceptanceID

    def IF(self, LValue, Operator, RValue, FirstF=True):
        if isinstance(RValue, (str,unicode)): test = "%s %s %s"   % (LValue, Operator, RValue)
        else:                                 test = "%s %s 0x%X" % (LValue, Operator, RValue)
        if FirstF: return "if( %s ) {\n"        % test
        else:      return "} else if( %s ) {\n" % test

    def END_IF(self, LastF=True):
        return { True: "}", False: "" }[LastF]

    def IF_INPUT(self, Condition, Value, FirstF=True):
        return self.IF("input", Condition, Value, FirstF)

    def IF_PRE_CONTEXT(self, FirstF, PreContextID, Consequence):

        if PreContextID == E_PreContextIDs.NONE:
            if FirstF: opening = "";             indent = "    ";     closing = ""
            else:      opening = "    else {\n"; indent = "        "; closing = "    }\n"
            return "%s%s%s%s\n" % (opening, indent, Consequence.replace("\n", "\n    "), closing)

        if FirstF: txt = "    if( "
        else:      txt = "    else if( "
        txt += self.PRE_CONTEXT_CONDITION(PreContextID)
        txt += " ) {\n        %s\n    }\n" % Consequence.replace("\n", "\n        ")
        return txt

    def PRE_CONTEXT_CONDITION(self, PreContextID):
        if PreContextID == E_PreContextIDs.BEGIN_OF_LINE: 
            return "me->buffer._character_before_lexeme_start == '\\n'"
        elif PreContextID == E_PreContextIDs.NONE:
            return "true"
        elif isinstance(PreContextID, (int, long)):
            return "pre_context_%i_fulfilled_f" % PreContextID
        else:
            assert False

    def ASSIGN(self, X, Y):
        return "%s = %s;" % (X, Y)

    def ACCESS_INPUT(self, txt=None, InputAction=E_InputActions.DEREF):
        code = {
            E_InputActions.DEREF:                "    %s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE()), 

            E_InputActions.INCREMENT:            "    %s\n" % self.INPUT_P_INCREMENT(), 
            
            E_InputActions.INCREMENT_THEN_DEREF: "    %s\n" % self.INPUT_P_INCREMENT() + \
                                                 "    %s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE()), 
            
            E_InputActions.DECREMENT:            "    %s\n" % self.INPUT_P_DECREMENT(), 
            
            E_InputActions.DECREMENT_THEN_DEREF: "    %s\n" % self.INPUT_P_DECREMENT() + \
                                                 "    %s\n" % self.ASSIGN("input", self.INPUT_P_DEREFERENCE()), 
        }[InputAction]

        if txt is None: return code

        txt.append(code)

    def STATE_ENTRY(self, txt, TheState, FromStateIndex=None, NewlineF=True, BIPD_ID=None):
        label = None
        if TheState.init_state_f:
            if   TheState.engine_type == E_EngineTypes.FORWARD: 
                index = TheState.index
            elif TheState.engine_type == E_EngineTypes.BACKWARD_INPUT_POSITION:
                label = "%s:\n" % self.LABEL_NAME_BACKWARD_INPUT_POSITION_DETECTOR(BIPD_ID) 
            else:
                index = TheState.index
        else:   
            index = TheState.index

        if label is None: label = self.LABEL(index, FromStateIndex, None, NewlineF)
        txt.append(label)

    def STATE_DEBUG_INFO(self, txt, StateIndex, InitStateForwardF):
        assert type(InitStateForwardF) == bool
        assert type(StateIndex) == long
        if InitStateForwardF: 
            txt.append("    __quex_debug(\"Init State\\n\");\n")
        txt.append("    __quex_debug_state(%i);\n" % StateIndex)
        return 

    def POSITION_REGISTER(self, Index):
        return "position[%i]" % Index

    def POSITIONING(self, Positioning, Register):
        if   Positioning == E_TransitionN.VOID: 
            return "me->buffer._input_p = position[%i];" % Register
        # "_input_p = lexeme_start_p + 1" is done by TERMINAL_FAILURE. 
        elif Positioning == E_TransitionN.LEXEME_START_PLUS_ONE: 
            return "" 
        elif Positioning > 0:     
            return "me->buffer._input_p -= %i; " % Positioning
        elif Positioning == 0:    
            return ""
        else:
            assert False 

    def SELECTION(self, Selector, CaseList, BreakF=False, CaseFormat="hex"):

        def __case(txt, item, Content=""):
            def format(N):
                return {"hex": "case 0x%X: ", 
                        "dec": "case %i: "}[CaseFormat] % N

            if isinstance(item, list):        
                for elm in item[:-1]:
                    txt.append(1) # 1 indentation
                    txt.append("%s\n" % format(elm))
                txt.append(1) # 1 indentation
                txt.append(format(item[-1]))

            elif isinstance(item, (int, long)): 
                txt.append(1) # 1 indentation
                txt.append(format(item))

            else: 
                txt.append(1) # 1 indentation
                txt.append("case %s: "  % item)

            if type(Content) == list: txt.extend(Content)
            elif len(Content) != 0:   txt.append(Content)
            if BreakF: txt.append(" break;\n")
            txt.append("\n")

        txt = [ 0, "switch( %s ) {\n" % Selector ]


        item, consequence = CaseList[0]
        for item_ahead, consequence_ahead in CaseList[1:]:
            if consequence_ahead == consequence: __case(txt, item)
            else:                                __case(txt, item, consequence)
            item        = item_ahead
            consequence = consequence_ahead

        __case(txt, item, consequence)

        txt.append(0)       # 0 indentation
        txt.append("}")
        return txt

    def REPLACE_INDENT(self, txt_list, Start=0):
        for i, x in enumerate(islice(txt_list, Start, None), Start):
            if isinstance(x, int): txt_list[i] = "    " * x

    def INDENT(self, txt_list, Add=1, Start=0):
        for i, x in enumerate(islice(txt_list, Start, None), Start):
            if isinstance(x, int): txt_list[i] += Add

    def VARIABLE_DEFINITIONS(self, VariableDB):
        assert type(VariableDB) != dict
        return cpp._local_variable_definitions(VariableDB.get()) 

    def RELOAD(self):
        txt = []
        txt.append(Address("$reload-FORWARD", None,  cpp_reload_forward_str))
        txt.append(Address("$reload-BACKWARD", None, cpp_reload_backward_str))
        return txt

cpp_reload_forward_str = """
    __quex_assert_no_passage();
__RELOAD_FORWARD:
    __quex_debug1("__RELOAD_FORWARD");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward)(&me->buffer, (QUEX_TYPE_CHARACTER_POSITION*)position, PositionRegisterN);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);
"""

cpp_reload_backward_str = """
    __quex_assert_no_passage();
__RELOAD_BACKWARD:
    __quex_debug1("__RELOAD_BACKWARD");
    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( QUEX_NAME(Buffer_is_begin_of_file)(&me->buffer) == false ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_backward)(&me->buffer);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);
"""

db["C++"] = LDB(CppBase)

#________________________________________________________________________________
# C
#    
db["C"] = copy(db["C++"])
db["C"].update([
    ("$token-default-file", "/token/CDefault.qx"),
    ("$token_template_file",    "/token/TXT-C"),
    ("$token_template_i_file",  "/token/TXT-C.i"),
    ("$analyzer_template_file", "/analyzer/TXT-C"),
    ("$file_extension",         ".c")
])

#________________________________________________________________________________
# Perl
#    
db["Perl"] = {
}

#________________________________________________________________________________
# Python
#    
db["Python"] = {
}

#________________________________________________________________________________
# Visual Basic 6
#    
db["VisualBasic6"] = {
    }

db["DOT"] = copy(db["C++"])
db["C"].update([
    ("$token-default-file", "/token/CDefault.qx"),
    ("$token_template_file",    "/token/TXT-C"),
    ("$token_template_i_file",  "/token/TXT-C.i"),
    ("$analyzer_template_file", "/analyzer/TXT-C"),
    ("$file_extension",         ".c"),
    ("$require-terminating-zero-preparation",  cpp.__require_terminating_zero_preparation),
    ("$comment-delimiters", [["/*", "*/", ""], ["//", "\n", ""], ["\"", "\"", "\\\""]]),
])
