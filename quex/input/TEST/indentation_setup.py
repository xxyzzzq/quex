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
    descr = counter.parse_indentation(sh)
    try:    
        descr = counter.parse_indentation(sh)
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
    test("[\\v\\a] => whitespace")
    test("[\\v\\a] => bytespace")
    test("[\\v\\a] => space;>")
    test("[\\v\\a] => newline;>")
    test("[\\v\\a] => suppressor;>")
    test("[\\v\\a] => bad;>")
    test("[\\v\\a] => comment;>")
    test(">")

elif "twice" in sys.argv:
    test("[\\v\\a] => whitespace;\n[\\t] => whitespace;>")
    test("[\\v\\a] => newline;\n[\\t] => newline;>")
    test("[\\v\\a] => suppressor;\n[\\t] => suppressor;>")
    test("[\\v\\a] => bad;\n[\\t] => bad;>")
    test("[\\v\\a] => comment;\n[\\t] => comment;>")

elif "intersection" in sys.argv:
    test("[abc] => whitespace;\n[cde] => newline;>")
    test("[abc] => whitespace;\n[cde] => suppressor;>")
    test("[abc] => whitespace;\n[cde] => bad;>")
    test("[abc] => whitespace;\n[cde] => comment;>")

    test("[abc] => bad;\n[cde] => newline;>")
    test("[abc] => bad;\n[cde] => suppressor;>")
    test("[abc] => bad;\n[cde] => whitespace;>")
    test("[abc] => bad;\n[cde] => comment;>")

    test("[abc] => newline;\n[cde] => bad;>")
    test("[abc] => newline;\n[cde] => suppressor;>")
    test("[abc] => newline;\n[cde] => whitespace;>")
    test("[abc] => newline;\n[cde] => comment;>")

    test("[abc] => suppressor;\n[cde] => bad;>")
    test("[abc] => suppressor;\n[cde] => whitespace;>")
    test("[abc] => suppressor;\n[cde] => newline;>")
    test("[abc] => suppressor;\n[cde] => comment;>")

    test("[abc] => comment;\n[cde] => bad;>")
    test("[abc] => comment;\n[cde] => whitespace;>")
    test("[abc] => comment;\n[cde] => newline;>")
    test("[abc] => comment;\n[cde] => suppressor;>")

elif "intersection-2" in sys.argv:

    test("abc*  => newline;\n[ce] => whitespace;>")
    test("abc*  => newline;\n[be] => whitespace;>")
    test("ac*b? => newline;\n[ce] => whitespace;>")
    test("ac*b  => newline;\n[ce] => whitespace;>")

elif "non-numeric" in sys.argv:
    test("/* empty will do */>")
