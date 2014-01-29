#! /usr/bin/env python
import sys
import os
sys.path.append(os.environ["QUEX_PATH"])

from StringIO import StringIO

import quex.input.files.counter as     counter
from   quex.engine.misc.file_in import EndOfStreamException, error_msg

if "--hwut-info" in sys.argv:
    print "Parse Indentation Setup;"
    print "CHOICES: basic, twice, intersection, intersection-2, non-numeric;"
    sys.exit()

# choice = sys.argv[1]
count_n = 0
def test(Text):
    global count_n
    count_n += 1

    if Text.find("\n") == -1:
        print "(%i) |%s|\n" % (count_n, Text)
    else:
        print "(%i)\n::\n%s\n::\n" % (count_n, Text)

    sh      = StringIO(Text)
    sh.name = "test_string"

    descr = None
    # descr = indentation.parse(sh, IndentationSetupF=True)
    try:    
        descr = counter.parse_indentation(sh, IndentationSetupF=True)
        pass

    except EndOfStreamException:
        error_msg("End of file reached while parsing 'indentation' section.", sh, DontExitF=True, WarningF=False)

    except:
        print "Exception!"

    if descr is not None: print descr
    print

if "basic" in sys.argv:

    test("[\\v\\a]")
    test("[\\v\\a] >")
    test("[\\v\\a] => grid")
    test("[\\v\\a] => trid")
    test("[\\v\\a] => grid>")
    test("[\\v\\a] => grid 4;>")
    test("[\\v\\a] => space;>")
    test("[\\v\\a] => space 0rXVI;>")
    test("[\\v\\a] => newline;>")
    test("[\\v\\a] => suppressor;>")
    test("[\\v\\a] => bad;>")
    test("[\\v\\a] => space;\n[\\t] => grid 10;")
    test("[\\v\\a] => space;\n[\\t] => grid 10;>")
    test(">")

elif "twice" in sys.argv:
    test("[\\v\\a] => space 10;\n[\\t] => space 10;>")
    test("[\\v\\a] => grid 10;\n[\\t] => grid 10;>")
    test("[\\v\\a] => newline;\n[\\t] => newline;>")
    test("[\\v\\a] => suppressor;\n[\\t] => suppressor;>")
    test("[\\v\\a] => bad;\n[\\t] => bad;>")

elif "intersection" in sys.argv:
    test("[abc] => space 10;\n[cde] => grid  4;>")
    test("[abc] => space 10;\n[cde] => newline;>")
    test("[abc] => space 10;\n[cde] => suppressor;>")
    test("[abc] => space 10;\n[cde] => bad;>")

    test("[abc] => grid 10;\n[cde] => space 1;>")
    test("[abc] => grid 10;\n[cde] => newline;>")
    test("[abc] => grid 10;\n[cde] => suppressor;>")
    test("[abc] => grid 10;\n[cde] => bad;>")

    test("[abc] => bad;\n[cde] => grid  10;>")
    test("[abc] => bad;\n[cde] => newline;>")
    test("[abc] => bad;\n[cde] => suppressor;>")
    test("[abc] => bad;\n[cde] => space;>")

    test("[abc] => newline;\n[cde] => grid  10;>")
    test("[abc] => newline;\n[cde] => space;>")
    test("[abc] => newline;\n[cde] => suppressor;>")
    test("[abc] => newline;\n[cde] => bad;>")

    test("[abc] => suppressor;\n[cde] => grid  10;>")
    test("[abc] => suppressor;\n[cde] => newline;>")
    test("[abc] => suppressor;\n[cde] => space;>")
    test("[abc] => suppressor;\n[cde] => bad;>")

elif "intersection-2" in sys.argv:

    test("abc* => newline;\n[ce] => space;>")
    test("abc* => newline;\n[be] => space;>")
    test("ac*b? => newline;\n[ce] => space;>")
    test("ac*b => newline;\n[ce] => space;>")

elif "non-numeric" in sys.argv:
    test("[\\v\\a] => grid variable;>")
    test("[\\v\\a] => grid variable kongo;>")
    test("[\\v\\a] => space variable2;>")
    test("[\\v\\a] => space variable 2;>")
    test("\\default => space variable;>")
    test(">")
    test("/* empty will do */>")
