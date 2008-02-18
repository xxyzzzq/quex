#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.frs_py.string_handling import trim

if "--hwut-info" in sys.argv:
    print "String Handling: Trim (replaced by string.strip(..))"
    sys.exit(0)

def test(String):
    print '"%s" \t-> "%s"' % (String, trim(String))


test("  hallo  ")
test("")
test("x")
test(" x")
test(" x ")
test("x ")


