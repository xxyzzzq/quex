#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])
import quex.blackboard         
from   quex.input.setup import NotificationDB         
import quex.output.core.languages.core as languages

quex.blackboard.setup.suppressed_notification_list = [ NotificationDB.warning_on_no_token_class_take_text ]
quex.blackboard.setup.output_token_class_file = ""
quex.blackboard.setup.token_class_name_space = ""
quex.blackboard.setup.token_class_name = "Token"
quex.blackboard.setup.language_db = languages.db["C++"]



from quex.input.files.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Constructor, Copy, Destructor;"
    print "CHOICES: Constructor, Constructor-1, Constructor-2, Destructor, Copy;"
    sys.exit(0)

def test(Tag, Txt):
    descr = TokenTypeDescriptorCore()
    sh = StringIO(Tag + Txt)
    sh.name = "string"
    print "-----------------------------"
    print "IN:"
    print "    [" + (Tag + Txt).replace("\n", "\n    ") + "]"
    print 
    print "OUT:"
    print 
    parse_section(sh, descr, [])
    try:
        pass
    except Exception, inst:
        print "Exception Caught: " + inst.__class__.__name__ 
    print TokenTypeDescriptor(descr)


if   "Constructor" in sys.argv:
    test("constructor", "{ The world is a { nice } place. }")

if   "Constructor-1" in sys.argv:
    test("constructor", "{  ")

if   "Constructor-2" in sys.argv:
    test("constructor", "{  The world is a /* } */ nice place }")

if   "Destructor" in sys.argv:
    test("destructor", "{ The world is a { nice } place. }")

if   "Copy" in sys.argv:
    test("copy", "{ The world is a { nice } place. }")




