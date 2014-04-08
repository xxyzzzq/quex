#! /usr/bin/env python
#
# PURPOSE: ASCII - codec. Testing the basic character counting functionality.
#
# -- With and withour reference-pointer counting (column_n += (input_p - reference_p)
#
# -- Spaces, Lines, and Grids.
# 
# -- *:               Dedicated Scenerios of Spaces, Grids, and Lines
#    *-wo-ReferenceP: Testing the reactions to all characters of the codec.       
#
# -- All tests use exactly the same input, so that the 'SAME' label for hwut 
#    tests can be applied.
#______________________________________________________________________________
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine    as     core
import quex.input.files.counter                as     counter_parser
from   quex.input.files.parser_data.counter    import CounterSetupLineColumn_Default
from   quex.engine.interval_handling           import NumberSet, Interval, NumberSet_All
import quex.engine.generator.languages.core    as     languages
import quex.engine.codec_db.core               as     codec_db
import quex.output.cpp.counter                 as     counter

from   quex.blackboard                         import setup as Setup, Lng
from   itertools                               import chain
from   os                                      import system
import subprocess
from   StringIO                                import StringIO

Setup.language_db = languages.db["C"]


if "--hwut-info" in sys.argv:
    # Information for HWUT
    #
    print "Character Counter: Default Implementation"
    print "CHOICES: ASCII, ASCII-wo-ReferenceP;"  
    print "SAME;"
    sys.exit(0)

test_list = [
    "",
    "a",
    "ab",
    "abc", 
    "abcd",
    "\t",
    "a\t",
    "ab\t",
    "abc\t",
    "abcd\t",
    "\t",
    "a\ta",
    "ab\ta",
    "abc\ta",
    "abcd\ta",
    "\n",
    "e\n",
    "\nf",
    "e\ng",
    "h\ni",
    "\t\n",
    "\n\t",
    "\t\n\t",
    "\t\n\t",
    "\t\nj",
    "\n\tk",
    "\t\n\tl",
    "\t\n\tm",
]

def prepare_test_input_file(TestStr):
    fh = open("./data/input.txt", "wb")
    fh.write(TestStr)
    fh.close()

def get_test_application(counter_db, ReferenceP):
    # (*) Generate Code 
    counter_function_name, \
    counter_str            = counter.get(counter_db.get_factory(NumberSet_All(), Lng.INPUT_P()), 
                                         "TEST_MODE")
    counter_str = counter_str.replace("static void", "void")

    # Make sure that the counter is implemented using reference pointer
    found_f = False
    for i, line in enumerate(counter_str.split("\n")):
        if line.find("reference_p") != -1:
            found_f = True
            break

    if ReferenceP:
        assert found_f, "Counter has not been setup using a reference pointer."
    else:
        assert not found_f, "Counter has been setup using a reference pointer."

    open("./data/test.c", "wb").write("#include <data/check.h>\n\n" + counter_str)

    # (*) Compile
    os.system("rm -f test")
    compile_str =   "gcc -Wall -I. -ggdb ./data/check.c ./data/test.c "     \
                  + " -D__QUEX_OPTION_COUNTER"                              \
                  + " -DDEF_COUNTER_FUNCTION='%s' " % counter_function_name \
                  + " -DDEF_FILE_NAME='\"data/input.txt\"' "                \
                  + " -DDEF_CHARACTER_TYPE=uint8_t "                        \
                  + " -o test" 
                  # + " -DDEF_DEBUG_TRACE " 

    print "## %s" % compile_str            
    os.system(compile_str)

def run():
    for i, test_str in enumerate(test_list):
        prepare_test_input_file(test_str)
        print "-------------------------------------------------"
        print "(%2i) Test String: [%s]" % (i, test_str.replace("\t", "\\t").replace("\n", "\\n"))
        print
        sys.stdout.flush()
        subprocess.call("./test")


if "ASCII" in sys.argv:
    counter_db  = None
    # Basic: With Reference Pointer Counting
    counter_db  = CounterSetupLineColumn_Default()
    reference_p = True
else:
    # Reference counter is not possible, since we have two space types
    spec_txt = """
       [\\x0A] => newline 1;
       [\\t]   => grid    4;
       [0-9]   => space   10;
       \else   => space   1;>
    """
    fh = StringIO(spec_txt)
    fh.name = "<string>"
    counter_db = counter_parser.parse_line_column_counter(fh)
    reference_p = False

get_test_application(counter_db, reference_p)
run()
    
