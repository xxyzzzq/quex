#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())
from helper import *


if "--hwut-info" in sys.argv:
    print "Skip-Range: DelimiterLength=2, Large Buffer"
    print "CHOICES: ANSI-C-PlainMemory, ANSI-C, Cpp, Cpp_StrangeStream;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C-PlainMemory", "ANSI-C", "Cpp", "Cpp_StrangeStream"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

Language          = sys.argv[1]
StrangeStream_str = ""
if Language.find("StrangeStream") != -1:
    StrangeStream_str = " -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION "


def test(TestStr):
    end_sequence = map(ord, "*/")
    code_str = create_range_skipper_code(Language, TestStr, end_sequence)
    compile_and_run(Language, code_str,
                    StrangeStream_str=StrangeStream_str)

test("abcdefg*/hijklmnop*/qrstuvw*/xyz*/ok")
test("*/hijklmnop*/qrstuvw*/xyz*/")
test("a*/h*/*/*/")


