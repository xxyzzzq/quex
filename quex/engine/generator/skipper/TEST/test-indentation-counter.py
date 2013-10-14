#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.engine.interval_handling                     import NumberSet, Interval
from   quex.engine.generator.TEST.generator_test         import __Setup_init_language_database
#from   generator_test                                   import compile_and_run, create_customized_analyzer_function, __Setup_init_language_database
from   helper                                            import *
from   quex.input.files.counter_setup                    import IndentationSetup
import quex.engine.generator.skipper.indentation_counter as     indentation_counter
from   quex.engine.analyzer.door_id_address_label        import dial_db
from   quex.engine.generator.languages.variable_db       import variable_db
from   quex.engine.interval_handling                     import NumberSet, Interval

from   copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Indentation Counting"
    print "CHOICES: Uniform, NonUniform, NonUniform-2;"
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

def test(TestStr, IndentationSetup, BufferSize=1024):
    Language = "Cpp"
    __Setup_init_language_database("Cpp")
    dial_db.clear()
    code_str = indentation_counter.do({"indentation_setup": IndentationSetup})

    txt = create_customized_analyzer_function("Cpp", TestStr, code_str, 
                                              QuexBufferSize=1024, 
                                              CommentTestStrF="", ShowPositionF=False, 
                                              EndStr=EndStr, MarkerCharList=map(ord, " :\t"),
                                              LocalVariableDB=deepcopy(variable_db.get()), 
                                              IndentationSupportF=True,
                                              TokenQueueF=True, 
                                              ReloadF=True)
    compile_and_run(Language, txt)

indent_setup = IndentationSetup()

if "Uniform" in sys.argv:

    indent_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 1)

    test("\n"
         "  a\n"
         "  :    b\n"
         "  :      c\n"
         "  :    d\n"
         "  :    e\n"
         "  :    h\n"
         "  i\n"
         "  j\n"
         , indent_setup)

elif "Uniform-Reloaded" in sys.argv:

    indent_setup.specify_space("[ ]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 1)

    test("\n"
         "  a\n"
         "                                     \n"
         "       b\n"
         "         c\n"
         "       d\n"
         "       e\n"
         "       h\n"
         "  i\n"
         "  j\n"
         , indent_setup, BufferSize=10)

elif "NonUniform" in sys.argv:
    indent_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 1)
    indent_setup.specify_grid("[\\t]", NumberSet(ord("\t")), 4)

    test("\n"
         "    a\n"     # 4 spaces
         "\tb\n"       # 0 space  + 1 tab = 4
         " \tc\n"      # 1 spaces + 1 tab = 4
         "  \td\n"     # 2 spaces + 1 tab = 4
         "   \te\n"    # 3 spaces + 1 tab = 4
         "    \tf\n"   # 4 spaces + 1 tab = 8
         "        g\n" # 8 spaces         = 8
         , indent_setup)


elif "NonUniform-2" in sys.argv:
    indent_setup.specify_space("[ \\:]", NumberSet([Interval(ord(" ")), Interval(ord(":"))]), 1)
    indent_setup.specify_grid("[\\t]", NumberSet(ord("\t")), 4)

    test("\n"
         "        a\n" # 8 spaces
         "\t \tb\n"    # tab + 1 + tab = 8
         "\t  \tc\n"   # tab + 2 + tab = 8
         "\t   \td\n"  # tab + 3 + tab = 8
         "\t    e\n"   # tab + 4       = 8
         , indent_setup)


