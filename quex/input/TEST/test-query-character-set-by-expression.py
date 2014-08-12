#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.core  as command_line
import quex.input.command_line.query as query


if "--hwut-info" in sys.argv:
    print "Quex Queries: Character Sets for Property Settings II"
    sys.exit(0)

def do(simulated_argv):
    if command_line.do(simulated_argv):
        query.do()

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
