#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.query as query


if "--hwut-info" in sys.argv:
    print "Quex Queries: Character Sets for Property Settings"
    sys.exit(0)


def test(simulated_argv):
    print "----------------------------------------------------------------------"
    print "ARGS: ", simulated_argv
    
    try:    query.do(simulated_argv)
    except: pass

    print
    try:    query.do(simulated_argv + ["--numeric"])
    except: pass

    print
    try:    query.do(simulated_argv + ["--numeric" , "--intervals"])
    except: pass
    print

test([ "", "--set-by-property", "Age" ])
test([ "", "--set-by-property", "Script=Runic" ])
test([ "", "--set-by-property", "bc=EN" ])
test([ "", "--set-by-property", "ASCII_Hex_Digit" ])
