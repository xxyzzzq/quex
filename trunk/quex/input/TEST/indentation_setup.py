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
    print "CHOICES: count, character_set;"
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
    #descr = indentation.do(sh)
    try:    
        descr = indentation.do(sh)
        pass

    except EndOfStreamException:
        error_msg("End of file reached while parsing 'indentation' section", sh, DontExitF=True)

    except:
        print "Exception!"
        pass

    print descr


    print

if "count" in sys.argv:
    test("{ tabulator   = 5; space = 1; }")
    test("{tabulator=bad;space=bad;}")
    test("{tabulator=grid 5;space=1;}")
    test("tabulator=grid 5;space=1;}")
    test("{tabulator=grid 5;space=1;")
    test("{fabulators=grid 5;space=1;")
    test("{tabulator==5;space=1;}")

else:
    test("{ define { tabulator  [\\r\\a] } }")
    test("{ define { tabulator  [\\r\\a] space [\\:]}}")
    test("{ define { fabulator  [\\r\\a] space [\\:]}}")
    test("{ fabulator = 34; define { fabulator  [\\r\\a] space [\\:]}}")
    test("{ fabulator = 34; }")
    test("{ \nfabulator = 34;\nfabulator = 12;\n}")
    test("{ define { \nspace  [\\r\\a] \nspace [\\:]\n  }\n}")
    test("{ define { \nspace  [\\:]    \ntabulator [\\:]\n  }\n}")
