#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.core  as command_line
from   quex.input.setup              import SETUP_INFO
import quex.blackboard               as blackboard


if "--hwut-info" in sys.argv:
    print "Quex Queries: Character Sets for Property Settings II"
    sys.exit(0)

def do(Argv):
    blackboard.setup.init(SETUP_INFO)
    assert False == command_line.do(Argv)

def test(simulated_argv):
    print "----------------------------------------------------------------------"
    print "ARGS: ", simulated_argv
    try:    do(["--set-by-expression"] + simulated_argv)
    except: pass
    print
    try:    do(["--set-by-expression"] + simulated_argv + ["--numeric"])
    except: pass
    print
    try:    do(["--set-by-expression"] + simulated_argv + ["--numeric" , "--intervals"])
    except: pass
    print

test(["intersection(\P{ID_Start}, \P{Script=Runic})"])
test(["intersection(\G{Nd}, \P{Script=Runic})"])
test(["intersection(\P{ID_Continue}, \P{Script=Khmer})"])
