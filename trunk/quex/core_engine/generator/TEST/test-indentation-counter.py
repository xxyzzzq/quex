#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.core_engine.interval_handling import NumberSet, Interval
from   generator_test                     import compile_and_run
from   quex.input.indentation_setup       import IndentationSetup
import quex.core_engine.generator.state_coder.indentation_counter as indentation_counter

if "--hwut-info" in sys.argv:
    print "Indentation Count: Different Buffer Sizes"
    print "CHOICES: Uniform, Non-Uniform;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2: 
    print "Argument not acceptable, use --hwut-info"
    sys.exit(0)

indentation_setup = IndentationSetup()

if "Uniform" in sys.argv:
    indentation_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 1)
else:
    indentation_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 4)
    indentation_setup.specify_grid("[\\t]", NumberSet(ord("\t")), 8)

TestStr  = "    :   :"
Language = "Cpp"
code_str = indentation_counter.do(indentation_setup)

print "##", code_str
# compile_and_run(Language, code_str)


