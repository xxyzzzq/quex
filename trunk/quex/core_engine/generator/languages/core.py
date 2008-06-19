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
from copy import copy
import quex.core_engine.generator.languages.cpp    as cpp
import quex.core_engine.generator.languages.python as python
from quex.frs_py.string_handling import blue_print

def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")
    
db = {}

label_db = \
{
    "$terminal":              lambda TerminalIdx: "TERMINAL_%s"              % __nice(TerminalIdx),
    "$terminal-EOF":          lambda NoThing:     "TERMINAL_END_OF_STREAM",
    "$terminal-DEFAULT":      lambda NoThing:     "TERMINAL_DEFAULT",
    "$terminal-with-preparation": lambda TerminalIdx: "TERMINAL_%s_WITH_PREPARATION" % __nice(TerminalIdx),
    "$terminal-general":      lambda BackWardLexingF: { 
                                        False: "TERMINAL_GENERAL",    
                                        True:  "TERMINAL_GENERAL_BACKWARD",
                                     }[BackWardLexingF],
    "$entry":                 lambda StateIdx:    "STATE_%s"          % __nice(StateIdx),
    "$drop-out":              lambda StateIdx:    "STATE_%s_DROP_OUT" % __nice(StateIdx),
    "$input":                 lambda StateIdx:    "STATE_%s_INPUT"    % __nice(StateIdx),
    "$re-start":              lambda NoThing:     "__REENTRY_PREPARATION",
    "$start":                 lambda NoThing:     "__REENTRY",
}
#________________________________________________________________________________
# C++
#    
db["C++"] = {
    "$MODUL$":        cpp,
    "$function_def":  "bool\n$$function_name$$(const int input)\n{\n", # still needed ?? fschaef 07y3m20d
    "$function_end":  "}\n",                                           # still needed ??
    "$if":            "if(",
    "$then":          ") {\n",
    "$elseif":        "else if(",
    "$endif":         "}\n",
    "$endif-else":    "} else {\n",
    "$end-else":      "}\n",
    "$else":          "else {",                                                     
    "$and":           "&&",
    "$loop-start-endless":  "while( 1 + 1 == 2 ) {\n",
    "$loop-end":            "}\n",
    "$continue":          "continue;\n",
    "$break":             "break;\n",
    "$if not BLC":        "if( input != QUEX_SETTING_BUFFER_LIMIT_CODE ) {\n",
    "$if EOF":            "if( QUEX_END_OF_FILE() ) {\n",
    "$if BOF":            "if( QUEX_BEGIN_OF_FILE() ) {\n",
    "$if pre-context":        lambda id: "if( pre_context_%s_fulfilled_f ) {\n" % repr(id).replace("L", ""),
    "$elseif pre-context":    lambda id: "else if( pre_context_%s_fulfilled_f ) {\n" % repr(id).replace("L", ""),
    "$if begin-of-line":      "if( me->begin_of_line_f ) {\n",
    "$elseif begin-of-line":  "else if( me->begin_of_line_f ) {\n",
    "$if <":              lambda value: "if( input < "  + value + ") {\n",
    "$if ==":             lambda value: "if( input == " + value + ") {\n",
    "$if !=":             lambda value: "if( input != " + value + ") {\n",
    #
    "$if >=":             lambda value: "if( input >= " + value + ") {\n",
    "$<":                 lambda left, right: left + " < " + right,
    "$==":                lambda left, right: left + " == " + right,
    "$!=":                lambda left, right: left + " != " + right,
    #
    "$comment":           lambda txt: "/* " + txt + " */",
    "$ml-comment":        lambda txt: "    /* " + txt.replace("\n", "\n     * ") + "\n     */",
    "$/*":     "//",
    "$*/":     "\n",
    "$*/\n":   "\n",    # make sure, that we do not introduce an extra '\n' in case that end of comment
    #                   # is followed directly by newline.
    "$local-variable-defs": cpp.__local_variable_definitions, 
    "$input":               "input",
    "$input/increment":     "QUEX_BUFFER_INCREMENT();",
    "$input/decrement":     "QUEX_BUFFER_DECREMENT();",
    "$input/get":           "QUEX_BUFFER_GET(input);",
    "$input/tell_position": lambda PositionStr: 
                            "QUEX_BUFFER_TELL_ADR(%s);\n" % PositionStr + \
                            "QUEX_DEBUG_ADR_ASSIGNMENT(\"tell position\", %s);" % PositionStr,
    "$input/seek_position": lambda PositionStr: 
                            "QUEX_BUFFER_SEEK_ADR(%s);\n" % PositionStr + \
                            "QUEX_DEBUG_ADR_ASSIGNMENT(\"seek position\", %s);" % PositionStr,
    "$return":              "return;",
    "$return_true":         "return true;",
    "$return_false":        "return false;",
    "$goto":                lambda Type, Argument=None:  "goto %s;" % label_db[Type](Argument),
    "$label-def":           lambda Type, Argument=None:  
                                "%s:\n"                                % label_db[Type](Argument) + \
                                "    QUEX_DEBUG_LABEL_PASS(\"%s\");\n" % label_db[Type](Argument),
    "$analyser-func":     cpp.__analyser_function,
    "$terminal-code":     cpp.__terminal_states,      
    "$drop-out-forward":  lambda StateIndex: 
                          "QUEX_SET_drop_out_state_index(%i);\n" % int(StateIndex) + \
                          "goto __FORWARD_DROP_OUT_HANDLING;\n",
    "$drop-out-backward": lambda StateIndex:              
                          "QUEX_SET_drop_out_state_index(%i);\n" % int(StateIndex) + \
                          "goto __BACKWARD_DROP_OUT_HANDLING;\n",
    "$compile-option":    lambda option: "#define %s\n" % option,
    "$assignment":        lambda variable, value:
                          "QUEX_DEBUG_ASSIGNMENT(\"%s\", \"%s\");\n" % (variable, value) + \
                          "%s = %s;\n" % (variable, value),
    "$set-last_acceptance": lambda value:
                          "QUEX_DEBUG_ASSIGNMENT(\"ACCEPTANCE\", \"%s\");\n" % value + \
                          "QUEX_SET_last_acceptance(%s);\n" % value,
    "$goto-last_acceptance": "QUEX_GOTO_last_acceptance();\n",
    #
    "$header-definitions":       cpp.__header_definitions,
    }

#________________________________________________________________________________
# C
#    
db["C"]  = copy(db["C++"])
db["C"]["$/*"] = "/*"
db["C"]["$*/"] = "*/\n"
db["C"]["$function_def"] = "const int\n$$function_name$$(const int input)\n{\n"
db["C"]["$return_true"]  = "return 1;"
db["C"]["$return_false"] = "return 0;"

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
    "$if":     "if ",
    "$then":   ":",
    "$if EOF": "if True:\n",
    "$if not BLC": "#if True:\n",
    "$if <":   lambda value: "if input < "  + value + ":\n",
    "$if ==":  lambda value: "if input == " + value + ":\n",
    "$if !=":  lambda value: "if input != " + value + ":\n",
    "$if >=":  lambda value: "if input >= " + value + ":\n",
    "$<":      lambda left, right: left + " < " + right,
    "$==":     lambda left, right: left + " == " + right,
    "$!=":     lambda left, right: left + " != " + right,
    "$>=":     ">=",
    "$endif":      "",                                                    
    "$else":       "else:",                                              
    "$endif-else": "else:\n",
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
    "$label":             "",   
    "$include":           lambda include_file: "#include <%s>" % include_file,
    "$debug-info-input":  "",
    "$header-definitions": "",
    "$goto-last_acceptance": "# QUEX_GOTO_last_acceptance();\n",
    "$drop-out": "# drop out\n",
    #
    "$goto":                lambda Type, Argument=None:  "return %s;" % Argument,
    "$label-def":           lambda Type, Argument=None:  
                                "#%s:\n"                                % label_db[Type](Argument) + \
                                "#    QUEX_DEBUG_LABEL_PASS(\"%s\");\n" % label_db[Type](Argument),
    "$drop-out-forward":  lambda StateIndex: 
                          "# QUEX_SET_drop_out_state_index(%i);\n" % int(StateIndex) + \
                          "# goto __FORWARD_DROP_OUT_HANDLING;\n",
    "$drop-out-backward": lambda StateIndex:              
                          "# QUEX_SET_drop_out_state_index(%i);\n" % int(StateIndex) + \
                          "# goto __BACKWARD_DROP_OUT_HANDLING;\n",
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


def replace_keywords(program_txt, LanguageDB, NoIndentF):
    """Replaces pseudo-code keywords with keywords of the given language."""

    txt = blue_print(program_txt, LanguageDB.items())

    if NoIndentF == False:
        # delete the last newline, to prevent additional indentation
        if txt[-1] == "\n": txt = txt[:-1]
        # indent by four spaces
        # (if this happens in recursively called functions nested indented blocks
        #  are correctly indented, see NumberSet::get_condition_code() for example)     
        txt = txt.replace("\n", "\n    ") + "\n"
    
    return txt          
