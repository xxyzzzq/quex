#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

from quex.input.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Options;"
    print "CHOICES: None, One, All;"
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
        parse_options(sh, descr)
    except Exception, inst:
        print "Exception Caught: " + inst.__class__.__name__ 
        pass
    print descr



if "One" in sys.argv:
    test("<head: my::math::complex G> {")
    for option in OptionList:
        test("<%s: uint8_t>  {" % option)
    exit(0)

elif "None" in sys.argv:
    test("  {")
    test("  ")

if "All" in sys.argv:
    txt = "<head: std::string name><head: std::vector<double> something>\n"
    for option in OptionList:
        txt += "<%s: uint8_t>  " % option 
    test(txt + "{")


