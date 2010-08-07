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
    print "CHOICES: basic;"
    sys.exit()

# choice = sys.argv[1]
count_n = 0
def test(Text):
    global count_n
    count_n += 1

    print "(%i) |%s|\n" % (count_n, Text)

    sh      = StringIO(Text)
    sh.name = "test_string"

    descr = None
    # descr = indentation.do(sh)
    try:    
        descr = indentation.do(sh)
        pass

    except EndOfStreamException:
        error_msg("End of file reached while parsing 'indentation' section", sh, DontExitF=True, WarningF=False)

    except:
        print "Exception!"

    if descr != None: print descr
    print

if "count" in sys.argv:
    test(" tabulator   = 5; space = 1; }")
    test("{tabulator=bad;space=bad;}")
    test("{tabulator=grid 5;space=1;}")
    test("tabulator=grid 5;space=1;}")
    test("{tabulator=grid 5;space=1;")
    test("{fabulators=grid 5;space=1;")
    test("{tabulator==5;space=1;}")
    test("{tabulator=grid 100; space= grid 500; otto= grid 25000; fritz = 500; define { otto [o] fritz [f] } }")
    test("{tabulator=grid 100; space= grid 500; otto= grid 25000; fritz = grid 500; define { otto [o] fritz [f] } }")
    test("{tabulator=grid 1; space= grid 1; otto= grid 1; fritz = 1; define { otto [o] fritz [f] } }")
    test("{tabulator= 4; space= 4; otto= 4; fritz = 4; define { otto [o] fritz [f] } }")

elif "count" in sys.argv:
    test("[\\r\\a]")
    test("{ define { tabulator  [\\r\\a] space [\\:]}}")
    test("{ define { fabulator  [\\r\\a] space [\\:]}}")
    test("{ fabulator = 34; define { fabulator  [\\r\\a] space [\\:]}}")
    test("{ fabulator = 34; }")
    test("{ \nfabulator = 34;\nfabulator = 12;\n}")
    test("{ define { \nspace  [\\r\\a] \nspace [\\:]\n  }\n}")
    test("{ define { \nspace  [\\:]    \ntabulator [\\:]\n  }\n}")
    test("{ define { \nspace  [\\:]    \ntabulator [a\\n]\n  }\n}")


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

