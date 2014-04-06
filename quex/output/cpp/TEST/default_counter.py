#! /usr/bin/env python
#
# PURPOSE: Testing the basic character counting functionality in ASCII. 
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
from   StringIO                                import StringIO

from   quex.blackboard                         import setup as Setup, Lng
from   itertools                               import chain
from   os                                      import system

Setup.language_db = languages.db["C"]


if "--hwut-info" in sys.argv:
    # Information for HWUT
    #
    print "Character Counter: Default Implementation"
    print "CHOICES: Default-UCS,    Default2-UCS,   Wild-UCS, "  \
                   "Default-cp037,  Default2-cp037, Wild-cp037, "\
                   "Default-UTF8,   Default2-UTF8,  Wild-UTF8, " \
                   "Default-UTF16,  Default2-UTF16, Wild-UTF16;"
    sys.exit(0)

elif "help" in sys.argv:
    # Generate a binary file that contains UCS coded code points of interest.
    # 
    fh = open("./data/example.utf32le", "wb")
    letter_set = chain(xrange(0x1, 0x10), xrange(0x83, 0x88), xrange(0x2026, 0x202B), xrange(0x5fe, 0x701), 
                       xrange(0xfffe, 0x110000, 0x1000), xrange(60, 64), xrange(0x12000, 0x12004))

    for letter in letter_set:
        fh.write("%c" %  (letter        & 0xFF))
        fh.write("%c" % ((letter >> 8)  & 0xFF))
        fh.write("%c" % ((letter >> 16) & 0xFF))
        fh.write("%c" % ((letter >> 32) & 0xFF))
    fh.close()

    system("iconv -f UTF32LE -t UTF8    ./data/example.utf32le -o ./data/example.utf8")
    system("iconv -f UTF32LE -t UTF16LE ./data/example.utf32le -o ./data/example.utf16le")
    fh = open("./data/example.cp037", "wb")
    for letter in range(0x100):
        print "#letter 0x%02X" % letter
        fh.write("%c" % letter)
    fh.close()
    sys.exit(0)

#______________________________________________________________________________
# 
# Test
#
choice, codec = sys.argv[1].split("-")

# (*) Interpret command line arguments ________________________________________
if   codec == "UCS":  
    Setup.buffer_codec_transformation_info = None
elif codec == "UTF8": 
    Setup.buffer_codec_transformation_info = "utf8-state-split"
elif codec == "UTF16":
    Setup.buffer_codec_transformation_info = "utf16-state-split"
else:                 
    Setup.buffer_codec_transformation_info = codec_db.CodecTransformationInfo(codec)

counter_db = None

if   choice == "Default":
    counter_db = CounterSetupLineColumn_Default()
elif choice == "Default2":
    spec_txt = """
       [\\x0A\\x0b\\x0c\\x85\\X2028\\X2029]      => newline 1;
       [\\x0d]                                   => newline 0;
       [\\t]                                     => grid    4;
       [\\X0600-\\X06FF]                         => space   3;
       [\\U010000-\\U10FFFF]                     => space   2;
    """
    print "#spec", spec_txt
elif choice == "Wild":
    spec     = [ "   [\\U%06X] => space 0x%i;\n" % (i, i % 4) for i in range(60, 64) + range(0x12000, 0x12004)]
    spec_txt = "".join(spec)
else:
    assert False, "Bad choice '%s'" % choice
    
# (*) Construct the Counter Database __________________________________________
Setup.buffer_codec = codec.lower()
buffer_element_type, Setup.tbuffer_element_size = {
        "UCS":   ("uint32_t", 4),
        "UTF8":  ("uint8_t", 1),
        "cp037": ("uint8_t", 1),
        "UTF16": ("uint16_t", 2),
}[codec]

# If 'counter_db' is not given as an object, then create one from
# the specification string.
if counter_db is None:
    spec_txt += ">"
    fh = StringIO(spec_txt)
    fh.name = "<string>"
    counter_db = counter_parser.parse_line_column_counter(fh)

# (*) Execute the Test ________________________________________________________

# (*) Get Couter Code
counter_function_name, counter_str = counter.get(counter_db.get_factory(NumberSet_All(), Lng.INPUT_P()), "TEST_MODE")
counter_str = counter_str.replace("static void", "void")

print "##" + counter_str.replace("\n", "\n##")
print "_____________________________________________________________________________"
sys.stdout.flush()

# (*) Execute Counter on given file

# open("./data/x.c", "wb").write("#include <data/check.h>\n\n" + counter_str)
open("./data/test.c", "wb").write("#include <data/check.h>\n\n" + counter_str)
file_extension = codec.lower()
if codec == "UCS":   file_extension = "utf32le"
if codec == "UTF16": file_extension = "utf16le"

# file_name = "./data/mini.%s" % file_extension
file_name = "./data/example.%s" % file_extension

os.system("rm -f test")
compile_str =   "gcc -Wall -I. -ggdb ./data/check.c ./data/test.c "     \
              + " -D__QUEX_OPTION_COUNTER"                              \
              + " -DDEF_COUNTER_FUNCTION='%s' " % counter_function_name \
              + " -DDEF_FILE_NAME='\"%s\"' "    % file_name             \
              + " -DDEF_CHARACTER_TYPE=%s "     % buffer_element_type   \
              + " -o test" \
              + " -DDEF_DEBUG_TRACE " 

print "## %s" % compile_str            
os.system(compile_str)
os.system("./test")
#os.remove("./data/test.c")

