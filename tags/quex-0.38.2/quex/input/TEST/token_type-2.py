#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

from quex.input.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Distinct Members;"
    print "CHOICES: None, One, Some, Forbidden, Error, Twice;"
    sys.exit(0)

def test(Txt):
    descr = TokenTypeDescriptor()
    sh = StringIO("distinct " + Txt)
    sh.name = "a string"
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
    print descr


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




