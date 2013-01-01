#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])
import quex.blackboard         
quex.blackboard.setup.token_class_take_text_check_f = False
quex.blackboard.setup.output_token_class_file = ""
quex.blackboard.setup.token_class_name_space = ""
quex.blackboard.setup.token_class_name = "Token"

from quex.input.files.token_type import *
from StringIO import StringIO

if "--hwut-info" in sys.argv:
    print "token_type: Buildt-In Members;"
    print "CHOICES: None, One, All, Forbidden, Forbidden-2, Error, Error-2, Twice;"
    sys.exit(0)

OptionList = ["id", "column_number", "line_number"]

def test(Txt):
    descr = TokenTypeDescriptorCore()
    sh = StringIO("standard " + Txt)
    sh.name = "string"
    print "-----------------------------"
    print "IN:"
    print "    [" + Txt.replace("\n", "\n    ") + "]"
    print 
    print "OUT:"
    print 
    parse_section(sh, descr, [])
    try:
        pass
    except Exception, inst:
        print "Exception Caught: " + inst.__class__.__name__ 
        pass

    print TokenTypeDescriptor(descr)


if "One" in sys.argv:
    for option in OptionList:
        test("{ %s : uint8_t; }" % option)
    exit(0)

elif "None" in sys.argv:
    test("  {")

elif "All" in sys.argv:
    txt = ""
    for option in OptionList:
        txt += "%s : uint8_t; " % option 
    test("{" + txt + "}")

elif "Forbidden"  in sys.argv:
    test("{ token_it : uint8_t; }")

elif "Forbidden-2"  in sys.argv:
    test("{ kolunm_numba : uint8_t; }")

elif "Error"  in sys.argv:
    test("{ id : uint8_t }")

elif "Error-2"  in sys.argv:
    test("{ id : std::string; }")

elif "Twice"  in sys.argv:
    txt = ""
    for option in OptionList:
        txt += "%s : uint8_t; " % option 
    test("{ " + txt + "%s : uint32_t;} " % OptionList[0])




