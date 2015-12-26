#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.core  as command_line
import quex.input.command_line.query as query


if "--hwut-info" in sys.argv:
    print "Quex Queries: Information about Properties"
    print "CHOICES: PropertyList, PropertyInfo"
    sys.exit(0)


if len(sys.argv) < 2 or sys.argv[1] not in ["PropertyInfo", "PropertyList" ]:
    print "Wrong command line argument. Call with --hwut-info for further info."
    sys.exit(0)

def do(simulated_argv):
    if command_line.do(simulated_argv):
        query.do()

if sys.argv[1] == "PropertyList":
    simulated_argv = [ "", "--property" ]

    do(simulated_argv)

else:

    simulated_argv = [ "", "--property", "Age" ]
    do(simulated_argv)

    simulated_argv = [ "", "--property", "Block" ]
    do(simulated_argv)

    simulated_argv = [ "", "--property", "Terminal_Punctuation" ]
    do(simulated_argv)

    simulated_argv = [ "", "--property", "Diacritic" ]
    do(simulated_argv)

    simulated_argv = [ "", "--property", "Bidi_Class" ]
    do(simulated_argv)
