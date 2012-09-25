#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling        import NumberSet, Interval
import quex.input.regular_expression.engine as     core
import quex.input.files.counter_setup       as     counter_setup
from   StringIO                             import StringIO

spec_txt = """
   [\\x0A\\x0b\\x0c\\x85\\X2028\\X2029\\x0d] => newline 1;
   [\\t]                                     => grid    4;
"""

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Characters of different horizontal sizes."
    print "CHOICES: Same, Different, TwoSet, Grid, Grid-BOL;"
    sys.exit(0)

choice = sys.argv[1]
if "TwoSet" in sys.argv:
    spec_txt += "   [a-zA-Z] => space 5;\n"
    spec_txt += "   [0-9]    => space 7;\n"
elif "Same" in sys.argv:
    spec_txt  = "   [\\x00-\\xFF] => space 66;\n"
elif "Different" in sys.argv:
    spec     = [ "    \\x%02X => space %i;\n" % (i, i) for i in xrange(2, 0x100)]
    spec_txt = "".join(spec)
elif choice in ["Grid", "Grid-BOL"]:
    spec_txt += "   [2byBY] => grid 5;\n"
else:
    assert False

# print "#spec:", spec_txt
spec_txt += ">"
    
fh = StringIO(spec_txt)
fh.name = "<string>"
lcc_setup = counter_setup.parse(fh, IndentationSetupF=False)
def adapt(db):
    return dict((count, parameter.get()) for count, parameter in db.iteritems())

counter_db = counter_setup.CounterDB(adapt(lcc_setup.space_db), 
                                     adapt(lcc_setup.grid_db), 
                                     adapt(lcc_setup.newline_db))


def test(TestString):
    global choice
    TestString = TestString.replace("\n", "\\n").replace("\t", "\\t")
    if choice == "Grid-BOL": TestString = "^%s" % TestString
    print ("expr. = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    pattern = core.do(TestString, {})
    pattern.prepare_count_info(counter_db)
    print ("info  = {\n    %s\n}\n" % str(pattern.count_info()).replace("\n", "\n    "))



#test('[0-9]+')
#sys.exit()
if choice not in ["Grid", "Grid-BOL"]:
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

else:
    # Some special tests for 'Grid'
    # Recall:  { 5: NumberSet([ Interval(ord(x)) for x in "2byBY" ]) }
    test('xxxxx2')
    test('xxxx2')
    test('xxx2')
    test('xx2')
    test('x2')
    test('2')
    test('xxxxx2|aaaaaaaaaa')
    test('xxxx2|aaaaa')
    test('xxx2|aaaaa')
    test('xx2|aaaaa')
    test('x2|aaaaa')
    test('2|aaaaa')
    test('xxxxx2|aaaaaaaaa')
    test('xxxx2|aaaa')
    test('xxx2|aaaa')
    test('xx2|aa')
    test('x2|a')
    test('2|aaaa')
    test('xxxxx2|22')
    test('xxxxx2')
    test('x2x2')
    test('x2x')
    print "##The result of the following should be '10' for both paths--meaning"
    print "##it could be computed beforehand, before run time."
    print "##However, it is 'VOID' which is safe, but not optimal. This is a"
    print "##consequence of handling the 'knot probem' where the number of paths"
    print "##increases exponentially. Benefit of optimal solution low and seldom."
    test('xxxxx2|x2x2')
