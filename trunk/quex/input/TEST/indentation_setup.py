#! /usr/bin/env python
import sys
import os

from StringIO import StringIO


sys.path.append(os.environ["QUEX_PATH"])
import quex.input.indentation_setup as     indentation
from   quex.core_engine.utf8        import map_unicode_to_utf8
from   quex.frs_py.file_in          import EndOfStreamException, error_msg

if "--hwut-info" in sys.argv:
    print "Parse Indentation Setup"
    sys.exit()

# choice = sys.argv[1]
count_n = 0
def test(Text):
    global count_n
    count_n += 1

    print "(%i) |%s|\n" % (count_n, Text)

    sh      = StringIO(Text)
    sh.name = "test_string"
    try:    
        descr = indentation.do(sh)
        print "spaces allowed =", repr(descr.spaces_setup.get())
        print "tabs           =", repr(descr.tabulators_setup.get())

    except EndOfStreamException:
        error_msg("End of file reached while parsing 'indentation' section", sh, DontExitF=True)

    except:
        pass

    print

test("{ tabulators   = 5; spaces = good; }")
test("{tabulators=bad;spaces=bad;}")
test("{tabulators=grid 5;spaces=good;}")
test("tabulators=grid 5;spaces=good;}")
test("{tabulators=grid 5;spaces=good;")
test("{fabulators=grid 5;spaces=good;")
test("{tabulators==5;spaces=good;}")


