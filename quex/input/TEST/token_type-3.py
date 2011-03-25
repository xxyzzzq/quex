#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])
import quex.input.setup         
quex.input.setup.setup.token_class_take_text_check_f = False
quex.input.setup.setup.output_token_class_file = ""
quex.input.setup.setup.token_class_name_space = ""
quex.input.setup.setup.token_class_name = "Token"

from quex.input.files.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Union Members;"
    print "CHOICES: None, One, One-2, Some, Some-2, Forbidden, Error, Twice, Twice-2;"
    sys.exit(0)

def test(Txt):
    descr = TokenTypeDescriptorCore()
    sh = StringIO("union " + Txt)
    sh.name = "string"
    print "-----------------------------"
    print "IN:"
    print "    [" + Txt.replace("\n", "\n    ") + "]"
    print 
    print "OUT:"
    print 
    try:
        parse_section(sh, descr, [])
    except Exception, inst:
        print "Exception Caught: " + inst.__class__.__name__ 
        pass
    print TokenTypeDescriptor(descr)


if   "One" in sys.argv:
    test("{ name : std::string; }")

elif "One-2" in sys.argv:
    test("""{ 
              { 
                 name : std::string; 
                 value : int; 
              }
            }
         """)

elif "None" in sys.argv:
    test("  {")

elif "Some" in sys.argv:
    test("{ name : std::string; number_list : std::vector<int>; }")

elif "Some-2" in sys.argv:
    test("""{ 
              { 
                 name : std::string; 
                 value : int; 
              }
              namer : std::string; number_list : std::vector<int>; 
            }""")

elif "Forbidden"  in sys.argv:
    test("{ id : uint8_t; }")

elif "Error"  in sys.argv:
    test("{ something : uint8_t }")

elif "Twice"  in sys.argv:
    test("{ name : std::string;\n name : std::vector<int>; }")

elif "Twice-2"  in sys.argv:
    test("""{ 
              { 
                 name : std::string; 
                 value : int; 
              }
              name : std::string; number_list : std::vector<int>; 
            }""")



