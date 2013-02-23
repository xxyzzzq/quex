#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())
from helper import *
from quex.engine.interval_handling import NumberSet, Interval
from quex.engine.generator.TEST.generator_test   import __Setup_init_language_database

if "--hwut-info" in sys.argv:
    print "Skip-Characters: Varrying Buffer Size"
    print "CHOICES: 3, 4, 5, 6, 7, 8;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2: 
    print "Argument not acceptable, use --hwut-info"
    sys.exit(0)

BS = int(sys.argv[1])

if BS not in [3, 4, 5, 6, 7, 8]:
    print "Argument not acceptable, use --hwut-info"
    sys.exit(0)

trigger_set = NumberSet([Interval(ord('a'), ord('z') + 1), 
                         Interval(ord('A'), ord('Z') + 1)])

Language = "Cpp"
__Setup_init_language_database(Language)


TestStr  = "abcdefg_HIJKLMNOP-qrstuvw'XYZ12ok3"

compile_and_run(Language, create_character_set_skipper_code(Language, TestStr, trigger_set, QuexBufferSize=BS))
TestStr  = "-hijklmnop_qrstuvw#xyz9"

compile_and_run(Language, create_character_set_skipper_code(Language, TestStr, trigger_set, QuexBufferSize=BS))

TestStr  = "aBcD8"

compile_and_run(Language, create_character_set_skipper_code(Language, TestStr, trigger_set, QuexBufferSize=BS))


