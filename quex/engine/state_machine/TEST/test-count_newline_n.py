#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as     core
import quex.input.files.counter_setup       as     counter_setup
from   StringIO                             import StringIO

spec_txt = """
   [\\x0A\\x0b\\x0c\\x85\\X2028\\X2029\\x0d] => newline 1;
   [\\t]                               => grid    4;
>"""

fh = StringIO(spec_txt)
fh.name = "<string>"
lcc_setup = counter_setup.parse(fh, IndentationSetupF=False)
def adapt(db):
    return dict((count, parameter.get()) for count, parameter in db.iteritems())

counter_db = counter_setup.CounterDB(adapt(lcc_setup.space_db), 
                                     adapt(lcc_setup.grid_db), 
                                     adapt(lcc_setup.newline_db))
if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Newlines"
    sys.exit(0)
    
def old_test(TestString):
    TestString = TestString.replace("\n", "\\n").replace("\t", "\\t")
    print "expression           = " + TestString
    pattern = regex.do(TestString, {})
    print "fixed newline number = ", pattern.newline_n
    print "fixed character number = ", pattern.character_n

def test(TestString):
    global counter_db

    #if "BeginOfLine" in sys.argv:
    #    TestString = "^%s" % TestString
    TestString = TestString.replace("\n", "\\n").replace("\t", "\\t")
    print ("expr. = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    pattern = core.do(TestString, {})
    pattern.prepare_count_info(counter_db, None)
    print ("info  = {\n    %s\n}\n" % str(pattern.count_info()).replace("\n", "\n    "))

#test('[ \t\n]')
#sys.exit()

test('[0-9]+')
test('"1\n\n\n3"')
test('"1\n\n\n3"|"A\n\n\nC"')
test('"1\n\n\n34"|"A\n\n\nC"')
test('"1\n\n\n34"|"A\n\n\nC\n"')
test('"1\n\n\n3\n"|"A\n\n\nC\n"')
test('"1\n"("1\n"?)')
test('"1\n"')
test('[ \t\n]')
test('[ \t\n]+')
test('"\n\n"')
test('(\n\n)+')
test('(\n|\n)+')
test('X(\n|\n)*')
test('X(\n|\n)?')
test('"1\n"+')
test('X"1\n"*')
test('X"1\n"?')

test('"1\n\n\n3"+')
test('X"1\n\n\n3"?')
test('X"1\n\n\n3"*')

test('a\n\n\nc("1\n\n\n3"+)')
test('a\n\n\nc("1\n\n\n3"?)')
test('a\n\n\nc("1\n\n\n3"*)')

test('a\n\n\nc("1\n\n\n3"+)x\n\n\nz')
test('a\n\n\nc("1\n\n\n3"?)x\n\n\nz')
test('a\n\n\nc("1\n\n\n3"*)x\n\n\nz')

test('a\n\n\nc("1\n\n\n3"|"A\n\n\nC")x\n\n\nz')
print "## The current algorithm does not consider the refreshing nature of newline."
print "## If a node is reached with two different column counts, then the colomn count"
print "## is considered 'void', even if a newline undoes the column count later and"
print "## all later counts end in acceptance with the same count."
test('a\n\n\nc("1\n\n\n3"|"A\n\n\nC\n")x\n\n\nz')
test('a\n\n\nc("1\n\n\n3"|"A\n\n\nC")+x\n\n\nz')
test('a\n\n\nc("1\n\n\n3"|"A\n\n\nC")?x\n\n\nz')
test('\na\n\n\nc\n("1\n\n\n3"|"A\n\nC\n")*\nx\n\n\nz\n')

test('"a"|"c"|"e"|"g"')
test('"a"|"\n"|"e"|"g"')
test('X("a"|"\n"*|"e"|"g")')
test('"a\ne"|"\n\n"')

test('A\n\n\nC("12\n\n\n"|("A\n\n\nC"|"X\n\n\nZ"))"12\n\n\n"("\n\n\nAA"|"\n\n\nBB"|"CC\n\n\n")X\n\n\nZ')
test('A\n\n\nC("12\n\n\n"|("A\n\n\nCD"|"X\n\n\nZ"))"12\n\n\n"("\n\n\nAA"|"\n\n\nBB"|"CC\n\n\n")X\n\n\nZ')
test('"\n"{4}("a\n\ne"|"\n\n")')

test('"\n123"')
test('"1\n23"|"A\nBC"')
test('"1\n234"|"A\nBC"')

# quex version >= 0.49.1: only treat core pattern; no pre and post-conditions
if False:
    test('"12\n"/"Z"')
    test('"1\n3"/"Z"')
    test('"12\n"+/"Z"')
    test('"1\n3"+/"Z"')
    test('("1\n23"|"A\nC")/"Z"')
    test('"12\n"/"ABC"|"XYZ"')
    test('"12\n"/"ABC"|"X"*')
    test('"12\n"/"ABC"|"X"?')
    test('"12\n"/"ABC"|""')
    test('"12\n"/"X\nZ"+')

    test('"a"/"\n"/"b"')
    test('x/(y|\n)/z')
    test('"a"/b/c|\n')
    test('"a\n"/b\nc|\n+')


