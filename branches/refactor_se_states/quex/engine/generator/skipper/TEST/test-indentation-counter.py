#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.input.regular_expression.construct           import Pattern
from   quex.engine.interval_handling                     import NumberSet, Interval
from   quex.engine.counter                               import ParserDataIndentation
from   quex.engine.analyzer.door_id_address_label        import dial_db
from   quex.engine.generator.code.base                   import SourceRef_VOID
from   quex.engine.generator.languages.variable_db       import variable_db
from   quex.engine.generator.TEST.generator_test         import __Setup_init_language_database
from   quex.engine.interval_handling                     import NumberSet, Interval

from   helper                                            import *

from   StringIO import StringIO
from   copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Indentation Counting"
    print "CHOICES: Uniform, NonUniform, NonUniform-2;"
    sys.exit(0)

if len(sys.argv) < 2: 
    print "Argument not acceptable, use --hwut-info"
    sys.exit(0)

def test(TestStr, ISetup, BufferSize=1024):
    Language = "Cpp"
    ISetup.finalize() # StringIO(""))
    txt = create_indentation_handler_code(Language, TestStr, ISetup, BufferSize, TokenQueueF=True)
    compile_and_run(Language, txt)

indent_setup = ParserDataIndentation(SourceRef_VOID)

def get_Pattern(ValueList):
    return Pattern.from_character_set(NumberSet([ Interval(ord(x)) for x in ValueList ]))

if "Uniform" in sys.argv:
    indent_setup.specify("whitespace", get_Pattern(" :"), SourceRef_VOID)

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
    indent_setup.specify("whitespace", get_Pattern(" :"), SourceRef_VOID)

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
    indent_setup.specify("whitespace", get_Pattern(" :\t"), SourceRef_VOID)

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
    indent_setup.specify("whitespace", get_Pattern(" :\t"), SourceRef_VOID)

    test("\n"
         "        a\n" # 8 spaces
         "\t \tb\n"    # tab + 1 + tab = 8
         "\t  \tc\n"   # tab + 2 + tab = 8
         "\t   \td\n"  # tab + 3 + tab = 8
         "\t    e\n"   # tab + 4       = 8
         , indent_setup)


