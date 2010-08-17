#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.core_engine.interval_handling import NumberSet, Interval
from   generator_test                     import compile_and_run, create_customized_analyzer_function
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

def test(TestStr, IndentationSetup):
    end_sequence = map(ord, "*/")

    code_str, local_variable_db = indentation_counter.do(IndentationSetup)

    txt = create_customized_analyzer_function("Cpp", TestStr, code_str, 
                                              QuexBufferSize=1024, CommentTestStrF="", ShowPositionF=False, 
                                              EndStr="", MarkerCharList="",
                                              LocalVariableDB=local_variable_db)
    compile_and_run(Language, txt)

indentation_setup = IndentationSetup()

if "Uniform" in sys.argv:
    indentation_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 1)
else:
    indentation_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 4)
    indentation_setup.specify_grid("[\\t]", NumberSet(ord("\t")), 8)

TestStr  = "    :   :"
Language = "Cpp"
code_str = indentation_counter.do(indentation_setup)

test("   :   ", indentation_setup)
# test("\t", indentation_setup)
# test("\t\t", indentation_setup)
# test("\t\t", indentation_setup)

# print "##", code_str
# compile_and_run(Language, code_str)


