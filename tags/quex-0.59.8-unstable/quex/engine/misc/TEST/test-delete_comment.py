#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.misc.file_in import delete_comment

if "--hwut-info" in sys.argv:
    print "File Input: Function delete_comment(...)"
    sys.exit(0)

def test(Text, Opener, Closer):
    try:
        accumulated_text = delete_comment(Text, Opener, Closer) 
    except:
        print "ERROR"
        return

    print "##-----------------------------------------------------------------------"
    print "## Comment:", Opener, Closer.replace("\n", "\\n")
    print Text
    print "##"
    print accumulated_text + "[[END]]"
    print "##"


test(" This is a simple test }",     "{", "}")
test(" This is a{simple}test }", "{", "}")

test(" This is a simple test */",       "/*", "*/")
test(" This is a-/*simple*/+test */", "/*", "*/")
test(" This is a-/*simple*/+", "/*", "*/")
test(" This is a-/*simple*/", "/*", "*/")

test(" This is a-//simple test \n",      "//", "\n")
test(" This is a-//simple*/test*/\n+", "//", "\n")
