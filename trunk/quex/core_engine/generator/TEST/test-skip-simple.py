#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.core_engine.generator.skip_code as skip_code
from   quex.core_engine.generator.languages.core import db
from   generator_test import create_main_function, \
                             compile_and_run

if "--hwut-info" in sys.argv:
    print "Plain Range Skipping: DelimiterLength=2, Large Buffer"
    print "CHOICES: ANSI-C-PlainMemory, ANSI-C, Cpp;"
    print "SAME;"
    sys.exit(0)

Language = sys.argv[1]
if not (Language in ["ANSI-C-PlainMemory", "ANSI-C", "Cpp"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

end_sequence = map(ord, "*/")

def create_code(Language, TestStr, EndSequence, QuexBufferSize=1024):
    reached_str  = '    printf("next letter: <%c>\\n", (char)(*(me->buffer._input_p + 1)));\n'
    reached_str += '    return true;\n'
    end_str      = '    printf("end\\n");'
    end_str     += '    return false;\n'

    txt  = "#define QUEX_CHARACTER_TYPE uint8_t\n"
    txt += "#define QUEX_TOKEN_ID_TYPE  bool\n"  
    if Language != "Cpp": txt += "#define __QUEX_SETTING_PLAIN_C\n"
    txt += "#include <quex/code_base/template/Analyser>\n"
    txt += "#include <quex/code_base/template/Analyser.i>\n"
    txt += "\n"
    if Language == "Cpp": txt += "using namespace quex;\n"
    txt += "bool  Mr_UnitTest_analyser_function(QuexAnalyser* me)\n"
    txt += "{\n"
    txt += "    QUEX_CHARACTER_POSITION_TYPE* post_context_start_position    = 0x0;\n"
    txt += "    QUEX_CHARACTER_POSITION_TYPE  last_acceptance_input_position = 0x0;\n"
    txt += "    QUEX_CHARACTER_TYPE           input                          = 0x0;\n"
    txt += skip_code.get_range_skipper(end_sequence, db["C++"], 0, end_str)
    txt += "__REENTRY_PREPARATION:\n"
    txt += "    " + reached_str
    txt += "}\n"

    txt += create_main_function(Language, TestStr, QuexBufferSize)

    return txt

TestStr  = "abcdefg*/hijklmnop*/qrstuvw*/xyz*/ok"

compile_and_run(Language, create_code(Language, TestStr, end_sequence))

TestStr  = "*/hijklmnop*/qrstuvw*/xyz*/"

compile_and_run(Language, create_code(Language, TestStr, end_sequence))

TestStr  = "a*/h*/*/*/"

compile_and_run(Language, create_code(Language, TestStr, end_sequence))


