#! /usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine        as     core
import quex.input.files.counter                    as     counter
from   quex.engine.codec_db.core                   import CodecDynamicInfo
import quex.engine.state_machine.utf8_state_split  as     utf8_state_split
import quex.engine.state_machine.utf16_state_split as     utf16_state_split
from   quex.blackboard import setup as Setup
from   StringIO                                    import StringIO

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Codec Engine"
    print "CHOICES: UTF8, UTF16;"
    sys.exit(0)
    
spec_txt = """
   [\\x02] => newline 1;
   [\\x03] => grid    4;
>"""

fh = StringIO(spec_txt)
fh.name    = "<string>"
counter_db = counter.parse_line_column_counter(fh)

def test(TestString):
    TestString = TestString.replace("\n", "\\n").replace("\t", "\\t")
    if "BeginOfLine" in sys.argv:
        TestString = "^%s" % TestString
    print ("expr. = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    pattern = core.do(TestString, {})

    # Prepare transformation info according to choice.
    if "UTF8" in sys.argv: trafo_info = Setup.buffer_codec_prepare("utf8", Module=utf8_state_split)
    else:                  trafo_info = Setup.buffer_codec_prepare("utf16", Module=utf16_state_split)

    # Count
    pattern.prepare_count_info(counter_db, trafo_info)
    print ("info  = {\n    %s\n}\n" % str(pattern.count_info()).replace("\n", "\n    "))

if "UTF8" in sys.argv:
    test("[\U000004-\U00007F]+")
    test("[\U000004-\U0007FF]+")
    test("[\U000004-\U00FFFF]+")
    test("[\U000004-\U1FFFFF]+")

    test("[\U000080-\U0007FF]+")
    test("[\U000080-\U00FFFF]+")
    test("[\U000080-\U1FFFFF]+")

    test("[\U000800-\U00FFFF]+")
    test("[\U000800-\U1FFFFF]+")

    test("[\U010000-\U1FFFFF]+")

if "UTF16" in sys.argv:
    test("[\U000004-\U00FFFF]+")
    test("[\U010000-\U1FFFFF]+")
    test("[\U000004-\U1FFFFF]+")

test('[ا-ي]+')
test('[ا-ي]{66}')
test('[a-zا-ي]+')
test('[a-zا-ي]{66}')
test('[\U011234-\U015678]+')
test('[\U011234-\U015678]{66}')
test('[a-z\U011234-\U015678]+')
test('[a-z\U011234-\U015678]{66}')
