#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.query as query


if "--hwut-info" in sys.argv:
    print "Quex Queries: Information about Properties"
    print "CHOICES: PropertyList, PropertyInfo"
    sys.exit(0)


if len(sys.argv) < 2 or sys.argv[1] not in ["PropertyInfo", "PropertyList" ]:
    print "Wrong command line argument. Call with --hwut-info for further info."
    sys.exit(0)

if sys.argv[1] == "PropertyList":
    simulated_argv = [ "", "--property" ]

    query.do(simulated_argv)

else:

    simulated_argv = [ "", "--property", "Age" ]
    query.do(simulated_argv)

    simulated_argv = [ "", "--property", "Block" ]
    query.do(simulated_argv)

    simulated_argv = [ "", "--property", "Terminal_Punctuation" ]
    query.do(simulated_argv)

    simulated_argv = [ "", "--property", "Diacritic" ]
    query.do(simulated_argv)

    simulated_argv = [ "", "--property", "Bidi_Class" ]
    query.do(simulated_argv)
