#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.query as query


if "--hwut-info" in sys.argv:
    print "Quex Queries: Character Sets for Property Settings II"
    sys.exit(0)


def test(simulated_argv):
    print "----------------------------------------------------------------------"
    print "ARGS: ", simulated_argv
    query.do(["--set-by-expression"] + simulated_argv)
    print
    query.do(["--set-by-expression"] + simulated_argv + ["--numeric"])
    print
    query.do(["--set-by-expression"] + simulated_argv + ["--numeric" , "--intervals"])
    print

test(["intersection(\P{ID_Start}, \P{Script=Runic})"])
test(["intersection(\G{Nd}, \P{Script=Runic})"])
test(["intersection(\P{ID_Continue}, \P{Script=Khmer})"])
