#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.query as query


if "--hwut-info" in sys.argv:
    print "Quex Queries:  Wildcard Property Values"
    sys.exit(0)

def test(simulated_arg):
    print "----------------------------------------------------------------------"
    print "ARGS: ", simulated_arg
    query.do(["--property-match",  simulated_arg])
    print


test("Name=*FIVE*")
test("Script=*Ar*")
