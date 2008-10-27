#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   generator_test import create_main_function, \
                             create_skipper_code, \
                             compile_and_run

if "--hwut-info" in sys.argv:
    print "Skip-Range: DelimiterLength=2, Large Buffer"
    print "CHOICES: ANSI-C-PlainMemory, ANSI-C, Cpp;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C-PlainMemory", "ANSI-C", "Cpp"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

Language     = sys.argv[1]
end_sequence = map(ord, "*/")

TestStr  = "abcdefg*/hijklmnop*/qrstuvw*/xyz*/ok"

compile_and_run(Language, create_skipper_code(Language, TestStr, end_sequence))

TestStr  = "*/hijklmnop*/qrstuvw*/xyz*/"

compile_and_run(Language, create_skipper_code(Language, TestStr, end_sequence))

TestStr  = "a*/h*/*/*/"

compile_and_run(Language, create_skipper_code(Language, TestStr, end_sequence))


