#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

from quex.input.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Buildt-In Members;"
    print "CHOICES: None, One, All, Forbidden, Error, Twice;"
    sys.exit(0)

OptionList = ["token_id", "column", "line"]

def test(Txt):
    descr = TokenTypeDescriptor()
    sh = StringIO(Txt)
    sh.name = "a string"
    print "-----------------------------"
    print "IN:"
    print "    [" + Txt.replace("\n", "\n    ") + "]"
    print 
    print "OUT:"
    print 
    try:
        parse_built_in_members(sh, descr, [])
    except Exception, inst:
        print "Exception Caught: " + inst.__class__.__name__ 
        pass
    print descr



if "One" in sys.argv:
    for option in OptionList:
        test("uint8_t : %s; {" % option)
    exit(0)

elif "None" in sys.argv:
    test("  {")
    test("  ")

elif "All" in sys.argv:
    txt = ""
    for option in OptionList:
        txt += "uint8_t : %s; " % option 
    test(txt + "{")

elif "Forbidden"  in sys.argv:
    test("uint8_t  : token_it;")

elif "Error"  in sys.argv:
    test("uint8_t  : token_it")

elif "Twice"  in sys.argv:
    txt = ""
    for option in OptionList:
        txt += "uint8_t : %s; " % option 
    test(txt + "uint32_t  : " + OptionList[0] + "; {")




