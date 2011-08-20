#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.misc.file_in import extract_identifiers_with_specific_prefix

if "--hwut-info" in sys.argv:
    print "File Input: Function extract_identifiers_with_specific_prefix(...)"
    sys.exit(0)

def test(Text, Prefix):
    try:
        finding_list = extract_identifiers_with_specific_prefix(Text, Prefix)
    except:
        print "ERROR"
        return

    print "##-----------------------------------------------------------------------"
    print "## Pefix: []" + Prefix + "[]"
    print Text + "[]"
    print "##"
    for name, line_n in finding_list:
        print "%02i: %s" % (line_n, name)
    print "##"


test("Quirk Q7",        "Q")
test("Quirk Q7 ",       "Q")
test("QUIRK-go\nQUIR7", "QUIRK")
test("QUIRKy\nQUIRK",   "QUIRK")
test("!Quirky\nQuiry",  "Quirk")

