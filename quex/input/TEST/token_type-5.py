#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])
import quex.blackboard         
import quex.engine.generator.languages.core as     languages
quex.blackboard.setup.language_db = languages.db["C++"]
quex.blackboard.setup.token_class_take_text_check_f = False
quex.blackboard.setup.output_token_class_file = ""
quex.blackboard.setup.token_class_name_space = ""
quex.blackboard.setup.token_class_name_safe = ""
quex.blackboard.setup.token_class_name = "Token"

from quex.input.files.token_type import *
from StringIO import StringIO


if "--hwut-info" in sys.argv:
    print "token_type: Class Name and Namespace;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6;"
    sys.exit(0)

def test(Txt):
    descr = TokenTypeDescriptorCore()
    txt = "{" + Txt + "}"
    sh = StringIO(txt)
    sh.name = "string"
    print "-----------------------------"
    print "IN:"
    print "    [ " + txt.replace("\n", "\n    ") + "]"
    print 
    print "OUT:"
    print 
    try:
        descr = parse(sh)
    except Exception, inst:
        print "Exception Caught: " + inst.__class__.__name__ 
    print TokenTypeDescriptor(descr)


arg = sys.argv[1]
test({ 
    "0": "name",
    "1": "name;",
    "2": "name =;",
    "3": "name = ispringen;",
    "3": "name = ispringen::;",
    "4": "name = deutschland::ispringen;",
    "5": "name = deutschland::ispringen::;",
    "6": "name = europa::deutschland::ispringen;",
    }[arg])




