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

EndStr = \
"""
#   define self (*me)
    self_send(QUEX_TKN_TERMINATION);
    return;
#   undef self
"""

def test(TestStr, IndentationSetup):
    code_str, local_variable_db = indentation_counter.do(IndentationSetup)

    txt = create_customized_analyzer_function("Cpp", TestStr, code_str, 
                                              QuexBufferSize=1024, CommentTestStrF="", ShowPositionF=False, 
                                              EndStr=EndStr, MarkerCharList=map(ord, " :"),
                                              LocalVariableDB=local_variable_db, 
                                              IndentationSupportF=True,
                                              TokenQueueF=True)
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

test("\n"
     "   :   a\n"
     "         b\n"
     "         c\n"
     "       d\n"
     "       e\n"
     "       h\n", indentation_setup)
# test("\t", indentation_setup)
# test("\t\t", indentation_setup)
# test("\t\t", indentation_setup)

# print "##", code_str
# compile_and_run(Language, code_str)


