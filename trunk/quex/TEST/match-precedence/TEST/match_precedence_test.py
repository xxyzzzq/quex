import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
sys.path.insert(0, os.getcwd())

import quex.input.files.mode             as mode
import quex.blackboard                   as blackboard
from   quex.engine.generator.action_info import UserCodeFragment
import quex.blackboard                   as blackboard

from   StringIO import StringIO

def do(TxtList, Op):
    mode.ModeDescription.registry_db.clear()
    for txt in TxtList:
        sh = StringIO(txt)
        sh.name = "<string>"
        mode.parse(sh)

    blackboard.initial_mode = UserCodeFragment("X", "<string>", 0)
    mode.finalize()

    for x in blackboard.mode_db.itervalues():
        print "Mode: '%s'" % x.name
        pap_list = x.get_pattern_action_pair_list()
        pap_list.sort(key=lambda x: x.pattern().sm.get_id())
        for i, pap in enumerate(pap_list):
            print "(%i) %s {%s}" % (i, pap.pattern_string(), pap.action().get_pure_code())
