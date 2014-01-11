import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
sys.path.insert(0, os.getcwd())

import quex.input.files.mode                       as     mode
from   quex.input.files.mode                       import Mode
import quex.blackboard                             as     blackboard
from   quex.engine.generator.code.base             import SourceRef
from   quex.engine.generator.code.core             import CodeUser
from   quex.engine.analyzer.door_id_address_label  import dial_db
import quex.engine.generator.languages.core        as     languages

blackboard.setup.language_db = languages.db["C++"]

from   StringIO import StringIO

def do(TxtList, Op):
    blackboard.mode_description_db.clear()
    for txt in TxtList:
        sh = StringIO(txt)
        sh.name = "<string>"
        mode.parse(sh)

    blackboard.initial_mode = CodeUser("X", SourceRef.from_FileHandle(sh))
    mode_finalize()

    for x in sorted(blackboard.mode_db.itervalues(), key=lambda x: x.name):
        print "Mode: '%s'" % x.name
        for i, pattern in enumerate(x.pattern_list):
            terminal = x.terminal_db[pattern.incidence_id()]
            print "(%i) %s {%s}" % (i, pattern.pattern_string(), "".join(terminal.pure_code()).strip())

def mode_finalize():
    for name, mode_descr in blackboard.mode_description_db.iteritems():        
        dial_db.clear()
        mode = Mode(mode_descr)
        blackboard.mode_db[name] = mode


