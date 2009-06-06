#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])
import quex.input.setup         
quex.input.setup.setup.token_type_disable_stringless_check_f = True


from quex.input.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Distinct Members;"
    print "CHOICES: None, One, Some, Forbidden, Error, Twice;"
    sys.exit(0)

def test(Txt):
    descr = TokenTypeDescriptorCore()
    sh = StringIO("distinct " + Txt)
    sh.name = "a string"
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

elif "None" in sys.argv:
    test("  {")

elif "Some" in sys.argv:
    test("{ name : std::string; number_list : std::vector<int>; }")

elif "Forbidden"  in sys.argv:
    test("{ id : uint8_t; }")

elif "Error"  in sys.argv:
    test("{ something : uint8_t }")

elif "Twice"  in sys.argv:
    test("{ name : std::string;\n name : std::vector<int>; }")




