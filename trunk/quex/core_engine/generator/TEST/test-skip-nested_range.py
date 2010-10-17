#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   generator_test import create_nested_range_skipper_code, \
                             compile_and_run

if "--hwut-info" in sys.argv:
    print "Skip-NestedRange: Delimiter Sizes 1 and 2;"
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


def test(TestStr, Opener="/*", Closer="*/"):
    open_sequence  = map(ord, Opener)
    close_sequence = map(ord, Closer)
    code_str = create_nested_range_skipper_code(Language, TestStr, open_sequence, close_sequence, QuexBufferSize=5)
    compile_and_run(Language, code_str,
                    StrangeStream_str=StrangeStream_str)

test("abc*/XYZ")
test("abc/*1*/XYZ*/xyz")
test("abc/*1/*2*/ABC*/DEF*/HIJ")
test("abc/**/*/xyz")
test("abc/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/**/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/xyz")
test("abc(((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((()))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))xyz", "(", ")")
test("abc/**//**//**//**//**//**//**//**/*/xyz")


