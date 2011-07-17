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
import quex.engine.generator.languages.cpp     as cpp
import quex.engine.generator.languages.python  as python
from   quex.engine.generator.languages.address import *
from   quex.engine.state_machine.state_core_info import PreContextIDs, EngineTypes, AcceptanceIDs, PostContextIDs
from   quex.blackboard                           import TargetStateIndices
from   quex.engine.analyzer.core                 import InputActions
from   quex.engine.misc.string_handling import blue_print
from   copy import deepcopy, copy

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
    "$local-variable-defs": cpp.__local_variable_definitions, 
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
    "$reload-definitions":   cpp.__reload_definitions,
    "$header-definitions":   cpp.__header_definitions,
    "$variable-definitions": cpp.__local_variable_definition,
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
    def __init__(self, DB):      self.update(DB)
    def __getattr__(self, Attr): return self[Attr]

    RETURN                  = "return;"
    UNREACHABLE             = "__quex_assert_no_passage();"
    ELSE                    = "} else {\n"
    INPUT_P_INCREMENT       = "++(me->buffer._input_p);"
    INPUT_P_TO_LEXEME_START = "QUEX_NAME(Buffer_seek_lexeme_start)(&me->buffer);"

    def GOTO(self, StateIndex):
        if StateIndex == TargetStateIndices.INIT_STATE_TRANSITION_BLOCK:
            return "goto INIT_STATE_TRANSITION_BLOCK;"
        elif StateIndex == TargetStateIndices.END_OF_PRE_CONTEXT_CHECK:
            return "goto END_OF_PRE_CONTEXT_CHECK;"
        else:
            return "goto _%i;" % StateIndex

    def GOTO_DROP_OUT(self, StateIndex):
        return get_address("$drop-out", StateIndex, U=True)

    def GOTO_RELOAD(self, TheState, ReturnStateIndexStr):
        if TheState.engine_type == EngineTypes.FORWARD: direction = "FORWARD"
        else:                                           direction = "BACKWARD"

        if TheState.init_state_forward_f:
            return "goto __RELOAD_INIT_STATE;" 

        elif TheState.engine_type == EngineTypes.BACKWARD_INPUT_POSITION:
            # There is never a reload on backward input position detection.
            # The lexeme to parse must lie inside the borders!
            return ""

        if ReturnStateIndexStr is not None: 
            state_reference = ReturnStateIndexStr
        else:                           
            state_reference = "QUEX_LABEL(%i)" % get_address("$entry", TheState.index, R=True)

        # Ensure that '__STATE_ROUTER' is marked as referenced
        get_label("$state-router", U=True)

        return "QUEX_GOTO_RELOAD(%s, %s, QUEX_LABEL(%i));" \
               % (get_label("$reload-%s" % direction, U=True),
                  state_reference,
                  get_address("$drop-out", TheState.index, U=True, R=True)) 

    def ACCEPTANCE(self, AcceptanceID):
        if AcceptanceID == AcceptanceIDs.FAILURE:
            return "QUEX_LABEL(%i)" % get_address("$terminal-FAILURE")
        else:
            return "%i" % AcceptanceID
    def GOTO_TERMINAL(self, AcceptanceID):
        if AcceptanceID == AcceptanceIDs.VOID: 
            return "QUEX_GOTO_TERMINAL(last_acceptance);"
        elif AcceptanceID == AcceptanceIDs.FAILURE:
            return "goto _%i; /* TERMINAL_FAILURE */" % get_address("$terminal-FAILURE")
        else:
            assert isinstance(AcceptanceID, (int, long))
            return "goto TERMINAL_%i;" % AcceptanceID

    def LABEL(self, StateIndex):
        if StateIndex in TargetStateIndices:
            return {
                TargetStateIndices.DROP_OUT:                    None,
                TargetStateIndices.RELOAD_PROCEDURE:            None,
                TargetStateIndices.INIT_STATE_TRANSITION_BLOCK: "INIT_STATE_TRANSITION_BLOCK:\n",
                TargetStateIndices.END_OF_PRE_CONTEXT_CHECK:    "END_OF_PRE_CONTEXT_CHECK:\n",
            }[StateIndex]
        return "_%i:\n" % StateIndex

    def IF_INPUT(self, Condition, Value, FirstF=True):
        if FirstF: return "if( input %s 0x%X ) {\n"        % (Condition, Value)
        else:      return "} else if( input %s 0x%X ) {\n" % (Condition, Value)

    def PRE_CONTEXT_CONDITION(self, PreContextID):
        if PreContextID == -1: 
            return "me->buffer._character_before_lexeme_start == '\\n'"
        elif isinstance(PreContextID, (int, long)):
            return "pre_context_%i_fulfilled_f" % PreContextID
        else:
            assert False

    def IF_PRE_CONTEXT(self, FirstF, PreContextList, Consequence):
        if PreContextList is None:                      return "    " + Consequence.replace("\n", "\n    ")
        if not isinstance(PreContextList, (list, set)): PreContextList = [ PreContextList ]
        if None in PreContextList:                      return "    " + Consequence.replace("\n", "\n    ")

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

    def ACCESS_INPUT(self, InputAction):
        return {
            InputActions.DEREF:                "    input = *(me->buffer._input_p);\n",
            InputActions.INCREMENT_THEN_DEREF: "    ++(me->buffer._input_p);\n"
                                               "    input = *(me->buffer._input_p);\n",
            InputActions.DECREMENT_THEN_DEREF: "    --(me->buffer._input_p);\n"
                                               "    input = *(me->buffer._input_p);\n",
        }[InputAction]

    def STATE_ENTRY(self, TheState):
        if TheState.init_state_forward_f:
            txt   = ["\n"]
            index = TargetStateIndices.INIT_STATE_TRANSITION_BLOCK
        elif TheState.init_state_f:
            txt   = ["\n"]
            index = TheState.index
        else:
            txt   = ["\n    %s\n" % self.UNREACHABLE ]
            index = TheState.index

        txt.append(self.LABEL(index))

        if TheState.init_state_forward_f: 
            txt.append("    __quex_debug_init_state();\n")
        elif TheState.engine_type == EngineTypes.FORWARD:
            txt.append("    __quex_debug_state(%i);\n" % TheState.index)
        else:
            txt.append("    __quex_debug_state_backward(%i);\n" % TheState.index)

        return "".join(txt)

    def POSITIONING(self, Positioning, Register):
        if   Positioning is None: 
            if Register == PostContextIDs.NONE: return "me->buffer._input_p = last_acceptance_position;"
            else:                               return "me->buffer._input_p = position[%i];" % Register
        elif Positioning > 0:   return "me->buffer._input_p -= %i; " % Positioning
        elif Positioning == 0:  return ""
        elif Positioning == -1: return "" # "_input_p = lexeme_start_p + 1" is done by TERMINAL_FAILURE. 
        else:                   assert False 

    def SELECTION(self, Selector, CaseList, BreakF=False):
        txt     = [ None ] * (len(CaseList) * 2 + 4) 
        txt[:2] = [ 0, "switch( %s ) {\n" % Selector ]

        line_end = " break;\n" if BreakF else "\n"

        i = 2
        for item, consequence in CaseList:
            txt[i] = 1   # 1 indentation
            i += 1
            if isinstance(item, (int, long)): txt[i] = "case %3i: %s%s" % (item, consequence, line_end)
            else:                             txt[i] = "case %s: %s%s"  % (item, consequence, line_end)
            i += 1

        txt[i]   = 0  # 0 indentation
        txt[i+1] = "}\n"
        return txt

    def REPLACE_INDENT(self, txt_list):
        for i, x in enumerate(txt_list):
            if isinstance(x, (int, long)): txt_list[i] = "    " * x

    def INDENT(self, txt_list):
        for i, x in enumerate(txt_list):
            if isinstance(x, (int, long)): txt_list[i] += 1

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

