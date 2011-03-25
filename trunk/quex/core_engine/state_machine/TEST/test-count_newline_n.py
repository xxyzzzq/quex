#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine         as regex
import quex.core_engine.state_machine.character_counter as counter

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Newlines"
    sys.exit(0)
    
def test(TestString):
    TestString = TestString.replace("\n", "\\n").replace("\t", "\\t")
    print "expression           = " + TestString
    sm = regex.do(TestString, {})
    print "fixed newline number = ", counter.get_newline_n(sm)

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


