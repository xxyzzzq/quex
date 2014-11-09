#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())
from helper                                    import *
from quex.engine.misc.interval_handling             import NumberSet, Interval
from quex.engine.generator.TEST.generator_test import __Setup_init_language_database

if "--hwut-info" in sys.argv:
    print "Skip-Characters: Large Buffer"
    print "CHOICES: ANSI-C-PlainMemory, ANSI-C, Cpp, Cpp_StrangeStream;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C-PlainMemory", "ANSI-C", "Cpp", "Cpp_StrangeStream"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

Language = sys.argv[1]
__Setup_init_language_database(Language)

StrangeStream_str = ""
if Language.find("StrangeStream") != -1:
    StrangeStream_str = " -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION "

trigger_set = NumberSet([Interval(ord('a'), ord('z') + 1), 
                         Interval(ord('A'), ord('Z') + 1)])

TestStr  = "abcdefg_HIJKLMNOP-qrstuvw'XYZ12ok3"

compile_and_run(Language, 
                create_character_set_skipper_code(Language, TestStr, trigger_set),
                StrangeStream_str=StrangeStream_str)

TestStr  = "-hijklmnop_qrstuvw#xyz9"

compile_and_run(Language, 
                create_character_set_skipper_code(Language, TestStr, trigger_set),
                StrangeStream_str=StrangeStream_str)

TestStr  = "aBcD8"

compile_and_run(Language, 
                create_character_set_skipper_code(Language, TestStr, trigger_set),
                StrangeStream_str=StrangeStream_str)


