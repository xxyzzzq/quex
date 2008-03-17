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

db = {}

#________________________________________________________________________________
# C++
#    
db["C++"] = {
    "$function_def":  "bool\n$$function_name$$(const int input)\n{\n", # still needed ?? fschaef 07y3m20d
    "$function_end":  "}\n",                                           # still needed ??
    "$if":     "if(",
    "$elseif": "else if(",
    "$then":   ") {",
    "$end":    "}",
    "$<":      "<",
    "$else":   "else {",                                                     
    "$and":    "&&",
    "$==":     "==",
    "$!=":     "!=",
    "$/*":     "//",
    "$*/":     "\n",
    "$*/\n":   "\n",    # make sure, that we do not introduce an extra '\n' in case that end of comment
    #                   # is followed directly by newline.
    "$input":               "input",
    "$input/get":           "QUEX_STREAM_GET(input);",
    "$input/get-backwards": "QUEX_STREAM_GET_BACKWARDS(input);",
    "$input/tell_position": cpp.__tell_position, 
    "$input/seek_position": "QUEX_STREAM_SEEK(last_acceptance_input_position);",        
    "$return":              "return;",
    "$return_true":         "return true;",
    "$return_false":        "return false;",
    "$transition":          cpp.__transition,
    "$label-definition":    cpp.__label_definition,
    "$acceptance-info":     cpp.__acceptance_info,      
    "$analyser-func":       cpp.__analyser_function,
    "$terminal-code":       cpp.__terminal_states,      
    "$pre-condition-ok":    cpp.__pre_context_ok,                                                  
    "$drop-out":            cpp.__state_drop_out_code,
    "$compile-option":    lambda option: "#define %s\n" % option,
    "$assignment":        lambda variable, value: "%s = %s;\n" % (variable, value),
    "$begin-of-line-flag-true":  "me->begin_of_line_f",
    #
    "$debug-info-input":    "__QUEX_DEBUG_INFO_INPUT(input);",
    #
    "$header-definitions":  cpp.__header_definitions,
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
    "$end":    "",
    "$<":      "<",
    "$==":     "==",
    "$!=":     "!=",
    "$>=":     ">=",
    "$endif": "",                                                    
    "$else":   "else:",                                              
    "$and":    "and",
    "$/*":     "#",
    "$*/":     "\n",  
    "$*/\n":   "\n",    # make sure, that we do not introduce an extra '\n' in case that end of comment
    #                   # is followed directly by newline.
    "$input":         "input",
    "$input/get":     "# TODO: getting input into parser",
    "$return_true":   "return True",
    "$return_false":  "return False",
    "$transition":        python.__transition, 
    "$label-definition":  python.__label_definition,
    "$goto-terminate":    python.__goto_terminal_state, 
    "$acceptance-info":   python.__note_acceptance,                    
    "$label":             "",   
    "$drop-out":          python.__state_drop_out_code,
    "$include":           lambda include_file: "#include <%s>" % include_file,
    "$debug-info-input":  "",
    "$header-definitions": "",
}

#________________________________________________________________________________
# Visual Basic 6
#    
db["VisualBasic6"] = {
    "$if":     "If",
    "$then":   "Then",
    "$end":    "End If",
    "$>=":     ">=",
    "$==":     "==",
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
