#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# PURPOSE: 
#
# Test character counting functionality for different codecs. The set of codecs
# include constant and dynamic character size codecs. For all codecs the
# 'collaboration' with grid and line number counting is tested.
#
# Codecs: ASCII, UTF8, UTF16, UTF32, CP737
# 
# Counter Databases: (1) Default, where a reference pointer counting can be 
#                        implemented.
#                    (2) A dedicated counter database where no reference 
#                        counter implementation is possible.
#
# For codecs with variable character sizes, the second number in the choice
# defines the number of chunks to be used for a letter. For example, 'utf_8-3'
# means that letters are used that consist of three bytes.
#
# Test cases are created from a 'test_list' (see variable below). For 'higher'
# codecs (UTF8, ...) the letters 'a', 'b', 'c' ... are sometimes replaced by
# letters from higher unicode code pages. For example, when three bytes are
# to be setup, letters from 0x800 to 0xFFFF are used for utf8. 
#
# The usage of a reference pointer in the generated code is verified at
# this point [RP]. 
#
# The setup of characters of the desired size is verified at this point [CS].
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine    as     core
import quex.input.files.counter                as     counter_parser
from   quex.input.files.parser_data.counter    import CounterSetupLineColumn_Default
from   quex.engine.counter                     import CountCmdFactory
from   quex.engine.interval_handling           import NumberSet, Interval, NumberSet_All
import quex.engine.generator.languages.core    as     languages
import quex.engine.codec_db.core               as     codec_db
import quex.output.cpp.counter                 as     counter
import quex.engine.state_machine.utf8_state_split  as utf8_state_split
import quex.engine.state_machine.utf16_state_split as utf16_state_split

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
        elif ChunkN == 2: db = { "a": u"ا",  "b": u"ب",  "c": u"ت",  "d": u"ى" }  # 2 byte letters
        elif ChunkN == 3: db = { "a": u"",  "b": u"",  "c": u"",  "d": u"" }  # 3 byte letters
        elif ChunkN == 4: db = { "a": u"𐅃", "b": u"𐅄", "c": u"𐅅", "d": u"𐅆" }     # 4 word letters
    elif Codec == "utf_16_le":
        chunk_size = 2 # [byte]
        if   ChunkN == 1: pass
        elif ChunkN == 2: db = { "a": u"𐅃", "b": u"𐅄", "c": u"𐅅", "d": u"𐅆" } # 2 word letters
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
    # [CS] Verify the setup of the specified character size.
    assert len(content) == chunk_n * chunk_size, "%s <-> %s" % (len(content), chunk_n * chunk_size)
    fh.close()

def get_test_application(counter_db, ReferenceP, CT):
    if   codec == "utf_32_le" or codec == "ascii":  
        Setup.buffer_codec = None
    elif codec == "utf_8": 
        Setup.buffer_codec = codec_db.CodecDynamicInfo(utf8_state_split)
    elif codec == "utf_16_le":
        Setup.buffer_codec = codec_db.CodecDynamicInfo(utf16_state_split)
    else:                 
        Setup.buffer_codec = codec_db.CodecTransformationInfo(codec)
    # (*) Generate Code 
    counter_function_name, \
    counter_str            = counter.get(CountCmdFactory.from_ParserDataLineColumn(counter_db, NumberSet_All(), Lng.INPUT_P()), 
                                         "TEST_MODE")
    counter_str = counter_str.replace("static void", "void")

    # Make sure that the counter is implemented using reference pointer
    found_n = 0
    for i, line in enumerate(counter_str.split("\n")):
        if line.find("reference_p") != -1:
            found_n += 1
            if found_n == 3: break


    # [RP] Verify that a reference pointer has been used or not used according 
    #      to what was specified.
    #      1. place: definition, 2. place: reference pointer set, 3. place: add.
    if ReferenceP:
        assert found_n >= 3, "Counter has not been setup using a reference pointer."
    else:
        assert found_n == 0, "Counter has been setup using a reference pointer."

    open("./data/test.c", "wb").write("#include <data/check.h>\n\n" + counter_str)

    # (*) Compile
    os.system("rm -f test")
    compile_str =   "gcc -Wall -Werror -I. -ggdb ./data/check.c ./data/test.c "     \
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
without_reference_p_f = (sys.argv[1].find("wo-ReferenceP") != -1)

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
    
os.remove("data/input.txt")
os.remove("test")
