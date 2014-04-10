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
    print "CHOICES: " \
          "ascii-1, ascii-1-wo-ReferenceP, " \
          "utf_16_le-1, utf_16_le-1-wo-ReferenceP, " \
          "utf_16_le-2, utf_16_le-2-wo-ReferenceP, " \
          "utf_32_le-1, utf_32_le-1-wo-ReferenceP, " \
          "cp737-1, cp737-1-wo-ReferenceP, " \
          "utf_8-1, utf_8-1-wo-ReferenceP, "   \
          "utf_8-2, utf_8-2-wo-ReferenceP, "   \
          "utf_8-3, utf_8-3-wo-ReferenceP, "   \
          "utf_8-4, utf_8-4-wo-ReferenceP;"  
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
    "a\n",
    "\na",
    "b\nb",
    "c\nc",
    "\t\n",
    "\n\t",
    "\t\n\t",
    "\t\n\t",
    "\t\na",
    "\n\tb",
    "\t\n\tc",
    "\t\n\td",
]

def prepare_test_input_file(TestStr, Codec, ChunkN):

    db = {}
    if Codec == "utf_8":
        chunk_size = 1 # [byte]
        if   ChunkN == 1: pass
        elif ChunkN == 2: db = { "a": u"ا",  "b": u"ب",  "c": u"ت",  "d": u"ى" }     # 2 byte letters
        elif ChunkN == 3: db = { "a": u"ठ",  "b": u"मु",  "c": u"ख",  "d": u"पृ" }     # 3 byte letters
        elif ChunkN == 4: db = { "a": u"化", "b": u"术", "c": u"与", "d": u"文" } # 4 byte letters
    elif Codec == "utf_16_le":
        chunk_size = 2 # [byte]
        if   ChunkN == 1: pass
        elif ChunkN == 2: db = { "a": u"化", "b": u"术", "c": u"与", "d": u"文" } # 2 word letters
    elif Codec == "utf_32_le":
        chunk_size = 4 # [byte]
    else:
        chunk_size = 1 # [byte]

    test_str = u""
    chunk_n  = 0
    for letter in TestStr:
        if letter in db: test_str += db[letter]; chunk_n += ChunkN
        else:            test_str += letter;     chunk_n += 1

    fh = codecs.open("./data/input.txt", "wb", Codec.lower())
    fh.write(test_str)
    fh.close()
    fh = open("./data/input.txt", "rb")
    content = fh.read()
    #print "#TestStr:", ["%x" % ord(x) for x in TestStr]
    #print "#content:", ["%x" % ord(x) for x in content]
    #assert len(content) == chunk_n * chunk_size, "%s <-> %s" % (len(content), chunk_n * chunk_size)
    fh.close()

def get_test_application(counter_db, ReferenceP, CT):
    if   codec == "utf_32_le" or codec == "ascii":  
        Setup.buffer_codec_transformation_info = None
    elif codec == "utf_8": 
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

def run(Codec, ChunkN):
    for i, test_str in enumerate(test_list):
        prepare_test_input_file(test_str, Codec, ChunkN)
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

fields  = sys.argv[1].split("-")
codec   = fields[0]
chunk_n = int(fields[1])
without_reference_p_f = sys.argv[1].find("wo-ReferenceP")

if without_reference_p_f:
    counter_db  = counter_db_wo_reference_p()
    reference_p = False
else:
    counter_db = CounterSetupLineColumn_Default()
    # UTF16 and UTF8 are dynamic length codecs. reference pointer based 
    # is impossible.
    if codec in ("utf_8", "utf_16_le"): reference_p = False
    else:                               reference_p = True

character_type = {
    "ascii":      "uint8_t",
    "utf_8":      "uint8_t",
    "utf_16_le":  "uint16_t",
    "utf_32_le":  "uint32_t",
    "cp737":      "uint8_t",
}[codec]

get_test_application(counter_db, reference_p, character_type)
run(codec, chunk_n)
    
