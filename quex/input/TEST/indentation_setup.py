#! /usr/bin/env python
import sys
import os

from StringIO import StringIO


sys.path.append(os.environ["QUEX_PATH"])
import quex.input.indentation_setup as     indentation
from   quex.core_engine.utf8        import map_unicode_to_utf8
from   quex.frs_py.file_in          import EndOfStreamException, error_msg

if "--hwut-info" in sys.argv:
    print "Parse Indentation Setup;"
    print "CHOICES: basic, twice, intersection;"
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
    descr = indentation.do(sh)
    try:    
        descr = indentation.do(sh)
        pass

    except EndOfStreamException:
        error_msg("End of file reached while parsing 'indentation' section.", sh, DontExitF=True, WarningF=False)

    except:
        print "Exception!"

    if descr != None: print descr
    print

if "basic" in sys.argv:
    test("[\\r\\a] => newline;>")

    test("[\\r\\a]")
    test("[\\r\\a] >")
    test("[\\r\\a] => grid")
    test("[\\r\\a] => trid")
    test("[\\r\\a] => grid>")
    test("[\\r\\a] => grid 4;>")
    test("[\\r\\a] => space;>")
    test("[\\r\\a] => space 0rXVI;>")
    test("[\\r\\a] => newline;>")
    test("[\\r\\a] => suppressor;>")
    test("[\\r\\a] => bad;>")
    test("[\\r\\a] => space;\n[\\t] => grid 10;")
    test("[\\r\\a] => space;\n[\\t] => grid 10;>")

elif "twice" in sys.argv:
    test("[\\r\\a] => space 10;\n[\\t] => space 10;>")
    test("[\\r\\a] => grid 10;\n[\\t] => grid 10;>")
    test("[\\r\\a] => newline;\n[\\t] => newline;>")
    test("[\\r\\a] => suppressor;\n[\\t] => suppressor;>")
    test("[\\r\\a] => bad;\n[\\t] => bad;>")

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

