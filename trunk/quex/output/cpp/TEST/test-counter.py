#! /usr/bin/env python
# -*- coding: utf-8 -*-
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
import codecs
import subprocess
from   StringIO                                import StringIO

Setup.language_db = languages.db["C"]


if "--hwut-info" in sys.argv:
    # Information for HWUT
    #
    print "Character Counter: Default Implementation"
    print "CHOICES: ASCII, ASCII-wo-ReferenceP, UTF16, UTF16-wo-ReferenceP, UTF32, UTF32-wo-ReferenceP;"  
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

def prepare_test_input_file(TestStr, Codec):
    fh = codecs.open("./data/input.txt", "wb", Codec.lower())
    fh.write(TestStr)
    fh.close()

    content = open("./data/input.txt", "rb").read()
    L  = len(content)
    Lt = len(TestStr)
    if   Codec is None:               assert L == Lt,     "%s <-> %s" % (L, Lt)
    elif L != 0 and Codec == "UTF16": assert L == Lt * 2, "%s <-> %s" % (L, Lt*2) 
    elif L != 0 and Codec == "UTF32": assert L == Lt * 4, "%s <-> %s" % (L, Lt*4) 

def get_test_application(counter_db, ReferenceP, CT):
    if   codec == "utf_32_le" or codec == "ascii":  
        Setup.buffer_codec_transformation_info = None
    elif codec == "UTF8": 
        Setup.buffer_codec_transformation_info = "utf8-state-split"
    elif codec == "utf_16_le":
        Setup.buffer_codec_transformation_info = "utf16-state-split"
    else:                 
        Setup.buffer_codec_transformation_info = codec_db.CodecTransformationInfo(codec)
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
                  + " -DDEF_CHARACTER_TYPE=%s " % CT                        \
                  + " -o test" 
                  # + " -DDEF_DEBUG_TRACE " 

    print "## %s" % compile_str            
    os.system(compile_str)

def run(Codec):
    for i, test_str in enumerate(test_list):
        prepare_test_input_file(test_str, Codec)
        print "-------------------------------------------------"
        print "(%2i) Test String: [%s]" % (i, test_str.replace("\t", "\\t").replace("\n", "\\n"))
        print
        sys.stdout.flush()
        subprocess.call("./test")

def counter_db_wo_reference_p():
    """RETURNS: A counter_db that makes it impossible to use a reference pointer.
    """
    # Reference counter is not possible, since we have two space types
    spec_txt = """
       [\\x0A] => newline 1;
       [\\t]   => grid    4;
       [0-9]   => space   10;
       \else   => space   1;>
    """
    fh = StringIO(spec_txt)
    fh.name        = "<string>"
    return counter_parser.parse_line_column_counter(fh)

if "ASCII" in sys.argv:
    # Basic: With Reference Pointer Counting
    counter_db     = CounterSetupLineColumn_Default()
    reference_p    = True
    codec          = "ascii"
    character_type = "uint8_t"

elif "ASCII-wo-ReferenceP" in sys.argv:
    counter_db     = counter_db_wo_reference_p()
    reference_p    = False
    codec          = "ascii"
    character_type = "uint8_t"

elif "UTF16" in sys.argv:
    counter_db     = CounterSetupLineColumn_Default()
    # UTF16 is a dynamic length codec and cannot be setup with reference pointer
    reference_p    = False
    codec          = "utf_16_le"
    character_type = "uint16_t"

elif "UTF16-wo-ReferenceP" in sys.argv:
    counter_db     = counter_db_wo_reference_p()
    reference_p    = False
    codec          = "utf_16_le"
    character_type = "uint16_t"

elif "UTF32" in sys.argv:
    # Basic: With Reference Pointer Counting
    counter_db     = CounterSetupLineColumn_Default()
    reference_p    = True
    codec          = "utf_32_le"
    character_type = "uint32_t"

elif "UTF32-wo-ReferenceP" in sys.argv:
    counter_db     = counter_db_wo_reference_p()
    reference_p    = False
    codec          = "utf_32_le"
    character_type = "uint32_t"

if "xxx" in sys.argv:
    test_list = ["a"] # make any special definition 


get_test_application(counter_db, reference_p, character_type)
run(codec)
    
