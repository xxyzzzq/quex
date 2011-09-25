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
import quex.engine.generator.languages.python    as     python
from   quex.engine.generator.languages.address   import *
from   quex.blackboard                           import E_StateIndices, E_EngineTypes, E_AcceptanceIDs, E_InputActions, E_TransitionN, E_PreContextIDs
from   copy                                      import copy

#________________________________________________________________________________
# C++
#    
def __close_namespace(NameList):
    txt = ""
    for name in NameList:
        txt += "} /* Closing Namespace '%s' */\n" % name
    return txt

def __open_namespace(NameList):
    txt = ""
    i = -1
    for name in NameList:
        i += 1
        txt += "    " * i + "namespace %s {\n" % name
    return txt

def __string_if_true(Value, Condition):
    if Condition: return Value
    else:         return ""

CppBase = {
    "$language":      "C++",
    "$comment-delimiters": [["/*", "*/", ""], ["//", "\n", ""], ["\"", "\"", "\\\""]],
    "$namespace-open":     __open_namespace,
    "$namespace-close":    __close_namespace,
    "$namespace-ref":      lambda NameList:
                           reduce(lambda x, y: x + "::" + y, [""] + NameList) + "::",
    "$class-member-def":   lambda TypeStr, MaxTypeNameL, VariableName, MaxVariableL:
                           "    %s%s %s;" % (TypeStr, " " * (MaxTypeNameL - len(TypeStr)), VariableName),
    "$MODUL$":        cpp,
    "$require-terminating-zero-preparation": cpp.__require_terminating_zero_preparation,
    "$function_def":  "bool\n$$function_name$$(const int input)\n{\n", # still needed ?? fschaef 07y3m20d
    "$function_end":  "}\n",                                           # still needed ??
    "$if":            "if(",
    "$then":          ") {\n",
    "$elseif":        "} else if(",
    "$endif":         "}\n",
    "$endif-else":    "} else {\n",
    "$end-else":      "}\n",
    "$else":          "else {",                                                     
    "$and":           " && ",
    "$or":            " || ",
    "$not":           lambda expr: "!( %s )" % expr,
    "$switch-block":  cpp.__get_switch_block,
    "$increment":     lambda variable: "++" + variable + ";",
    "$decrement":     lambda variable: "--" + variable + ";",
    "$loop-start-endless":    "while( 1 + 1 == 2 ) {\n",
    "$loop-end":              "}\n",
    "$continue":              "continue;\n",
    "$indentation_add":          cpp.__indentation_add,
    "$indentation_check_space":  cpp.__indentation_check_whitespace,
    "$break":                 "break;\n",
    "$not BLC":               "(input != QUEX_SETTING_BUFFER_LIMIT_CODE) ",
    "$BLC":                   "(input == QUEX_SETTING_BUFFER_LIMIT_CODE) ",
    "$EOF":                   "QUEX_NAME(Buffer_is_end_of_file)(&me->buffer)",
    "$BOF":                   "QUEX_NAME(Buffer_is_begin_of_file)(&me->buffer)",
    "$if pre-context":        lambda id: "if( pre_context_%s_fulfilled_f ) {\n" % repr(id).replace("L", ""),
    "$elseif pre-context":    lambda id: "else if( pre_context_%s_fulfilled_f ) {\n" % repr(id).replace("L", ""),
    "$if begin-of-line":      "if( me->buffer._character_before_lexeme_start == '\\n' ) {\n",
    "$elseif begin-of-line":  "else if( me->buffer._character_before_lexeme_start == '\\n' ) {\n",
    "$if <":              lambda value: "if( input < "  + value + ") {\n",
    "$if in-set":         cpp.__get_if_in_character_set,
    "$if in-interval":    cpp.__get_if_in_interval,
    "$if ==":             lambda value: "if( input == " + value + " ) {\n",
    "$elseif ==":         lambda value: "} else if( input == " + value + " ) {\n",
    "$if !=":             lambda value: "if( input != " + value + " ) {\n",
    #
    "$if >=":             lambda value: "if( input >= " + value + ") {\n",
    "$<":                 lambda left, right: " " + left + " < "  + right + " ",
    "$>=":                lambda left, right: " " + left + " >= " + right + " ",
    "$<=":                lambda left, right: " " + left + " <= " + right + " ",
    "$>":                 lambda left, right: " " + left + " > "  + right + " ",
    "$==":                lambda left, right: " " + left + " == " + right + " ",
    "$!=":                lambda left, right: " " + left + " != " + right + " ",
    #
    "$comment":           lambda txt: "/* " + txt + " */",
    "$ml-comment":        lambda txt: "    /* " + txt.replace("/*", "SLASH_STAR").replace("*/", "STAR_SLASH").replace("\n", "\n     * ") + "\n     */",
    "$/*":     "//",
    "$*/":     "\n",
    "$*/\n":   "\n",    # make sure, that we do not introduce an extra '\n' in case that end of comment
    #                   # is followed directly by newline.
    "$input":               "input",
    "$debug-print":         lambda txt: "__quex_debug(\"%s\");" % txt,
    "$mark-lexeme-start":   "me->buffer._lexeme_start_p = me->buffer._input_p;",
    "$input/add":           lambda Offset:      "QUEX_NAME(Buffer_input_p_add_offset)(&me->buffer, %i);" % Offset,
    "$input/increment":     "++(me->buffer._input_p);",
    "$input/decrement":     "--(me->buffer._input_p);",
    "$input/get":           "input = *(me->buffer._input_p);",
    "$input/get-offset":    lambda Offset:      "input = QUEX_NAME(Buffer_input_get_offset)(&me->buffer, %i);" % Offset,
    "$input/tell_position": lambda PositionStr: "%s = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer);" % PositionStr,
    "$input/seek_position": lambda PositionStr: "QUEX_NAME(Buffer_seek_memory_adr)(&me->buffer, %s);" % PositionStr,
    "$return":              "return;",
    "$return_true":         "return true;",
    "$return_false":        "return false;",
    "$goto":                 lambda Type, Argument=None:  "goto %s;" % label_db_get(Type, Argument, GotoTargetF=True),
    "$goto-pure":            lambda Argument:             "goto %s;" % label_db_register_usage(Argument),
    "$goto-template":        lambda TemplateStateIdx, StateKey: 
                             "template_state_key = %i; " % StateKey + \
                             "goto %s;\n" % label_db_get("$entry", TemplateStateIdx, GotoTargetF=True),
    "$goto-template-state-key":    lambda TemplateIdx: 
                                   "QUEX_TEMPLATE_GOTO_STATE_KEY(%i, template_state_key);" % TemplateIdx,
    "$label":                lambda Type, Argument=None: label_db_get(Type, Argument, GotoTargetF=True),
    "$label-pure":           lambda Label:                "%s:" % Label,
    "$label-def":            lambda Type, Argument=None:  "%s:" % label_db_get(Type, Argument), 
    "$debug-state":          lambda StateIdx, ForwardF: \
                                    { True:  "__quex_debug_state(%i);\n"          % StateIdx,
                                      False: "__quex_debug_state_backward(%i);\n" % StateIdx, }[ForwardF],
    "$debug-init-state":     "__quex_debug_init_state();\n",
    "$analyzer-func":        cpp.__analyzer_function,
    "$terminal-code":        cpp.__terminal_states,      
    "$compile-option":       lambda option: "#define %s\n" % option,
    "$assignment":           lambda variable, value: "%s = %s;\n" % (variable, value),
    "$goto-last_acceptance": "QUEX_GOTO_TERMINAL(last_acceptance);\n",
    #
    "$header-definitions":   cpp.__header_definitions,
    "$frame":                cpp.__frame_of_all,
    "$goto-mode":            lambda Mode: "QUEX_NAME(enter_mode)(&self, &" + Mode + ");",
    "$gosub-mode":           lambda Mode: "QUEX_NAME(push_mode)(&self, &" + Mode + ");",
    "$goup-mode":            lambda Mode: "QUEX_NAME(pop_mode)(&self);",                  # Must be function, w/o arg
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
    INPUT_P                 = "me->buffer._input_p"
    INPUT_P_INCREMENT       = "++(me->buffer._input_p);"
    PATH_ITERATOR_INCREMENT = "++(path_iterator);"
    INPUT_P_TO_LEXEME_START = "QUEX_NAME(Buffer_seek_lexeme_start)(&me->buffer);"

    def ADDRESS(self, StateIndex, FromStateIndex):
        if self.__analyzer is None:
            FromStateIndex = None
        elif self.__analyzer.engine_type != E_EngineTypes.FORWARD:
            FromStateIndex = None
        elif FromStateIndex is not None:
            if self.__analyzer.state_db.has_key(StateIndex) == False:
                # It must be a template/path walker state. Those are not real analyzer states
                # but little engines that can be entered via an address.
                FromStateIndex = None
            elif not self.__analyzer.state_db[StateIndex].entry.special_door_from_state(FromStateIndex):
                # If the entry of the target state is uniform (the same from every 'SourceState'),
                # then we do not need to goto it through a specific door (FromStateIndex = None).
                # If the 'Analyzer == None' we assume that all related states have 
                # independent_of_source_state entries.
                FromStateIndex = None

        result = get_address("$entry", (StateIndex, FromStateIndex), U=True, R=True)
        return result

    def ADDRESS_DROP_OUT(self, StateIndex):
        return get_address("$drop-out", StateIndex)

    def __label_name(self, StateIndex, FromStateIndex=None):
        if StateIndex in E_StateIndices:
            assert StateIndex != E_StateIndices.DROP_OUT
            assert StateIndex != E_StateIndices.RELOAD_PROCEDURE
            return {
                E_StateIndices.INIT_STATE_TRANSITION_BLOCK: "INIT_STATE_TRANSITION_BLOCK",
                E_StateIndices.END_OF_PRE_CONTEXT_CHECK:    "END_OF_PRE_CONTEXT_CHECK",
                E_StateIndices.ANALYZER_REENTRY:            "__REENTRY",
            }[StateIndex]

        return "_%i" % self.ADDRESS(StateIndex, FromStateIndex)

    def LABEL(self, StateIndex, FromStateIndex=None, NewlineF=True):
        label = self.__label_name(StateIndex, FromStateIndex)
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

    def GOTO(self, TargetStateIndex, FromStateIndex=None):
        # Only for normal 'forward analysis' the from state is of interest.
        # Because, only during forward analysis some actions depend on the 
        # state from where we come.
        result = "goto %s;" % self.__label_name(TargetStateIndex, FromStateIndex)
        return result

    def GOTO_DROP_OUT(self, StateIndex):
        return get_address("$drop-out", StateIndex, U=True)

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

    def ACCEPTANCE(self, AcceptanceID):
        if AcceptanceID == E_AcceptanceIDs.FAILURE: return "((QUEX_TYPE_ACCEPTANCE_ID)-1)"
        else:                                       return "%i" % AcceptanceID

    def IF(self, LValue, Operator, RValue, FirstF=True):
        if isinstance(RValue, (str,unicode)): test = "%s %s %s"   % (LValue, Operator, RValue)
        else:                                 test = "%s %s 0x%X" % (LValue, Operator, RValue)
        if FirstF: return "if( %s ) {\n"        % test
        else:      return "} else if( %s ) {\n" % test

    def IF_INPUT(self, Condition, Value, FirstF=True):
        return self.IF("input", Condition, Value, FirstF)

    def PRE_CONTEXT_CONDITION(self, PreContextID):
        if PreContextID == E_PreContextIDs.BEGIN_OF_LINE: 
            return "me->buffer._character_before_lexeme_start == '\\n'"
        elif PreContextID == E_PreContextIDs.NONE:
            return "true"
        elif isinstance(PreContextID, (int, long)):
            return "pre_context_%i_fulfilled_f" % PreContextID
        else:
            assert False

    def IF_PRE_CONTEXT(self, FirstF, PreContextList, Consequence):
        if not isinstance(PreContextList, (list, set)): PreContextList = [ PreContextList ]

        if E_PreContextIDs.NONE in PreContextList: 
            if FirstF: opening = "";             indent = "    ";     closing = ""
            else:      opening = "    else {\n"; indent = "        "; closing = "    }\n"
            return "%s%s%s%s\n" % (opening, indent, Consequence.replace("\n", "\n    "), closing)

        if FirstF: txt = "    if( "
        else:      txt = "    else if( "

        last_i = len(PreContextList) - 1
        for i, pre_context_id in enumerate(PreContextList):
            txt += self.PRE_CONTEXT_CONDITION(pre_context_id)
            if i != last_i: txt += " || "

        txt += " ) {\n        %s\n    }\n" % Consequence.replace("\n", "\n        ")
        return txt

    def ASSIGN(self, X, Y):
        return "%s = %s;" % (X, Y)

    def END_IF(self, LastF=True):
        return { True: "}", False: "" }[LastF]

    def ACCESS_INPUT(self, txt, InputAction):
        txt.append({
            E_InputActions.DEREF:                "    input = *(me->buffer._input_p);\n",
            E_InputActions.INCREMENT:            "    ++(me->buffer._input_p);\n",
            E_InputActions.INCREMENT_THEN_DEREF: "    ++(me->buffer._input_p);\n"
                                                 "    input = *(me->buffer._input_p);\n",
            E_InputActions.DECREMENT:            "    --(me->buffer._input_p);\n",
            E_InputActions.DECREMENT_THEN_DEREF: "    --(me->buffer._input_p);\n"
                                                 "    input = *(me->buffer._input_p);\n",
        }[InputAction])

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

        if label is not None: txt.append(label)
        else:                 txt.append(self.LABEL(index, FromStateIndex, NewlineF))

    def STATE_DEBUG_INFO(self, txt, StateIndex, InitStateForwardF):
        assert type(InitStateForwardF) == bool
        assert type(StateIndex) == long
        if InitStateForwardF: txt.append("    __quex_debug_init_state();\n")
        else:                 txt.append("    __quex_debug_state(%i);\n" % StateIndex)
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

    def REPLACE_INDENT(self, txt_list):
        for i, x in enumerate(txt_list):
            if isinstance(x, (int, long)): txt_list[i] = "    " * x

    def INDENT(self, txt_list, Add=1):
        for i, x in enumerate(txt_list):
            if isinstance(x, (int, long)): txt_list[i] += Add

    def VARIABLE_DEFINITIONS(self, VariableDB):
        return cpp._local_variable_definitions(VariableDB.get()) 

    def RELOAD(self):
        txt = []
        txt.append(Address("$reload-FORWARD", None,  cpp_reload_forward_str))
        txt.append(Address("$reload-BACKWARD", None, cpp_reload_backward_str))
        return txt

cpp_reload_forward_str = """
    __quex_assert_no_passage();
__RELOAD_FORWARD:
    __quex_debug("__RELOAD_FORWARD");

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
    __quex_debug("__RELOAD_BACKWARD");
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
db["C"]["$token-default-file"]     = "/token/CDefault.qx"
db["C"]["$token_template_file"]    = "/token/TXT-C"
db["C"]["$token_template_i_file"]  = "/token/TXT-C.i"
db["C"]["$analyzer_template_file"] = "/analyzer/TXT-C"
db["C"]["$file_extension"]         = ".c"

#________________________________________________________________________________
# Perl
#    
db["Perl"] = copy(db["C"])
db["Perl"]["$function_def"] = "sub $$function_name$$ {\n    input = shift\n"

#________________________________________________________________________________
# Python
#    
db["Python"] = {
    "$function_def":  "def $$function_name$$(input):\n",
    "$function_end":  "\n",                                                  
    "$debug-print":   lambda txt: "quex_debug_print(me.buffer, \"%s\")" % txt,
    "$if":     "if ",
    "$then":   ":",
    "$if EOF": "if True:\n",
    "$not BLC": "True",
    "$if <":   lambda value: "if input < "  + value + ":\n",
    "$if in-set":       python.__get_if_in_character_set,
    "$if in-interval":  python.__get_if_in_interval,
    "$if ==":  lambda value: "if input == " + value + ":\n",
    "$if !=":  lambda value: "if input != " + value + ":\n",
    "$if >=":  lambda value: "if input >= " + value + ":\n",
    "$<":      lambda left, right: left + " < " + right,
    "$==":     lambda left, right: left + " == " + right,
    "$!=":     lambda left, right: left + " != " + right,
    "$>=":     ">=",
    "$endif":      "\n",                                                    
    "$else":       "else:",                                              
    "$endif-else": "else:\n",
    "$switch-block":  python.__get_switch_block,
    "$end-else":   "",
    "$and":    "and",
    "$comment": lambda txt: "# " + txt + "\n",
    "$/*":     "#",
    "$*/":     "\n",  
    "$*/\n":   "\n",    # make sure, that we do not introduce an extra '\n' in case that end of comment
    #                   # is followed directly by newline.
    "$input":         "input",
    "$input/get":     "# TODO: getting input into parser",
    "$input/increment":     "# TODO: getting input into parser",
    "$return_true":   "return True",
    "$return_false":  "return False",
    "$label-definition":  python.__label_definition,
    "$goto-terminate":    python.__goto_terminal_state, 
    "$acceptance-info-fw":   lambda x, y: "",
    "$acceptance-info-bw":   lambda x, y: "",
    "$acceptance-info-bwfc": lambda x, y: "",
    "$label":                lambda Type, Argument: label_db_get(Type, Argument, GotoTargetF=True),
    "$include":              lambda include_file: "#include <%s>" % include_file,
    "$debug-info-input":  "",
    "$header-definitions": "",
    "$goto-last_acceptance": "# QUEX_GOTO_last_acceptance();\n",
    "$reload": "# reload\n",
    #
    "$goto":                lambda Type, Argument=None:  "return %s;" % Argument,
    "$goto-pure":           lambda Argument:             "return %s;" % Argument,
    "$label-def":           lambda Type, Argument=None:  
                                "#%s:\n"                                % label_db[Type](Argument) + \
                                "#    QUEX_DEBUG_LABEL_PASS(\"%s\");\n" % label_db[Type](Argument),
}

#________________________________________________________________________________
# Visual Basic 6
#    
db["VisualBasic6"] = {
    "$if":     "If",
    "$then":   "Then",
    "$endif":  "End If",
    "$>=":     ">=",
    "$==":     lambda left, right: left + " == " + right,
    "$!=":     lambda left, right: left + " <> " + right,
    "$input":  "input",
    "$return_true":  "$the_function = True: Exit Function",
    "$return_false": "$the_function = True: Exit Function",
    }

db["DOT"] = {
        "$token-default-file":     "/token/CDefault.qx",
        "$token_template_file":    "/token/TXT-C",
        "$token_template_i_file":  "/token/TXT-C.i",
        "$analyzer_template_file": "/analyzer/TXT-C",
        "$file_extension":         ".dot",
    "$code_base":               "/quex/code_base/",
    "$require-terminating-zero-preparation": cpp.__require_terminating_zero_preparation,
    "$comment-delimiters": [["/*", "*/", ""], ["//", "\n", ""], ["\"", "\"", "\\\""]],
}
