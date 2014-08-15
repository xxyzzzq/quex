#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.core  as command_line
import quex.input.command_line.query as query
import quex.input.setup              as setup
import quex.blackboard               as blackboard


if "--hwut-info" in sys.argv:
    print "Quex Queries: Character Sets for Property Settings"
    sys.exit(0)


def do(simulated_argv):
    blackboard.setup.init(setup.SETUP_INFO)
    assert not command_line.do(simulated_argv)

def test(simulated_argv):
    print "----------------------------------------------------------------------"
    print "ARGS: ", simulated_argv
    
    try:    do(simulated_argv)
    except: pass

    print
    try:    do(simulated_argv + ["--numeric"])
    except: pass

    print
    try:    do(simulated_argv + ["--numeric" , "--intervals"])
    except: pass
    print

    try:    do(simulated_argv + ["--names"])
    except: pass


test([ "", "--set-by-property", "Age" ])
test([ "", "--set-by-property", "Script=Runic" ])
test([ "", "--set-by-property", "bc=EN" ])
test([ "", "--set-by-property", "ASCII_Hex_Digit" ])
