#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.frs_py.file_in import read_until_closing_bracket
from StringIO            import StringIO

if "--hwut-info" in sys.argv:
    print "File Input: Function read_until_closing_bracket(...)"
    sys.exit(0)

def test(Text, Opener, Closer, IgnoreRegions=[]):
    sh = StringIO(Text)
    try:
        accumulated_text = read_until_closing_bracket(sh, Opener, Closer, IgnoreRegions) 
    except:
        print "ERROR"
        return

    print "##-----------------------------------------------------------------------"
    print Text
    print "##"
    print accumulated_text + "[[END]]"
    print "##"


test(" This is a simple test }", "{", "}")

test(" This is a { simple } test }", "{", "}")

test(""" This is a REM } after newline
         { simple } test }""", 
     "{", "}", 
     [["REM", "\n"]])

test(""" This is a REM very funny}
         { simple } test }""", 
     "{", "}", 
     [["REM", "\n"]])

test(""" This is a /* {very}}}}} funny} */ { simple } test }""", 
     "{", "}", 
     [["/*", "*/"]])

test(" This is a \" simple \\\" \" test}", "", "}", [["\"", "\""]])
