#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as     core
import quex.input.files.counter_setup       as     counter_setup
from   quex.input.files.counter_db          import CounterDB
from   StringIO                             import StringIO

spec_txt = """
   [\\x0A\\x0b\\x0c\\x85\\X2028\\X2029\\x0d] => newline 1;
   [\\t]                               => grid    4;
>"""

fh = StringIO(spec_txt)
fh.name    = "<string>"
lcc_setup  = counter_setup.parse(fh, IndentationSetupF=False)
counter_db = CounterDB(lcc_setup)

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Characters"
    print "CHOICES: Normal, BeginOfLine;"
    sys.exit(0)
    
def test(TestString):
    TestString = TestString.replace("\n", "\\n").replace("\t", "\\t")
    if "BeginOfLine" in sys.argv:
        TestString = "^%s" % TestString
    print ("expr. = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    pattern = core.do(TestString, {})
    pattern.prepare_count_info(counter_db, None)
    print ("info  = {\n    %s\n}\n" % str(pattern.count_info()).replace("\n", "\n    "))

test('[0-9]+')
test('"123"')
test('"123"|"ABC"')
test('"1234"|"ABC"')
test('"123"+')
test('X"123"?')
test('"123"?X')
test('"123"*X')
test('X"123"*')

test('abc("123"+)')
test('abc("123"?)')
test('abc("123"*)')

test('abc("123"+)xyz')
test('abc("123"?)xyz')
test('abc("123"*)xyz')

test('abc("123"|"ABC")xyz')
test('abc("123"|"ABCD")xyz')
test('abc("123"|"ABC")+xyz')
test('abc("123"|"ABC")?xyz')
test('abc("123"|"ABC")*xyz')

test('"a"|"c"|"e"|"g"')
test('X("a"|"x"?|"e"|"g")')
test('"a"|"x"+|"e"|"g"')
test('X("a"|"x"*|"e"|"g")')

test('abc("123"|("ABC"|"XYZ"))"123"("AAA"|"BBB"|"CCC")xyz')
test('abc("123"|("ABCD"|"XYZ"))"123"("AAA"|"BBB"|"CCC")xyz')

test('[: intersection([\X900-\X970], \P{ID_Start}) :]([: intersection([\X900-\X970], \P{ID_Continue}) :]*)')

# quex version >= 0.49.1: only treat core pattern; no pre and post-conditions
if False:
    test('"123"/"Z"')
    test('"123"+/"Z"')
    test('("123"|"ABC")/"Z"')
    test('"123"/"ABC"|"XYZ"')
    test('"123"/"ABC"|"X"*')
    test('"123"/"ABC"|"X"?')
    test('"123"/"ABC"|""')
    test('"123"/"XYZ"+')

    test('a/x*')
    test('a|ab/x*')
    test('(a|ab)/x')
    test('(a|abc)/xy')
    test('"1"/"XZ"+')
