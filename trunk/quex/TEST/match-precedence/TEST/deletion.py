#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
sys.path.insert(0, os.getcwd())

import match_precedence_test as test

if "--hwut-info" in sys.argv:
    print "Checking DELETE marks internally.;"
    print "CHOICES: 3-begin, 3-mid, 3-end, 2-begin, 2-end, 1, Nonsense," \
                   "derived-3-begin, derived-3-mid, derived-3-end, derived-2-begin, derived-2-end, derived-1, derived-Nonsense," \
                   "before, derived-before;"
    sys.exit()

derived = None
if   "3-begin" in sys.argv:
    base = "X { A {} B {} C {} A DELETION; }"
elif "3-mid" in sys.argv:
    base = "X { A {} B {} C {} B DELETION; }"
elif "3-end" in sys.argv:
    base = "X { A {} B {} C {} C DELETION; }"
elif "2-begin" in sys.argv:
    base = "X { A {} B {} A DELETION; }"
elif "2-end" in sys.argv:
    base = "X { A {} B {} B DELETION; }"
elif "1" in sys.argv:
    base = "X { A {} A DELETION; }"
elif "Nonsense" in sys.argv:
    base = "X { A {} Nonsense DELETION; }"
elif   "derived-3-begin" in sys.argv:
    base    = "X { A {} B {} C {} }"
    derived = "Y : X { A DELETION; }"
elif "derived-3-mid" in sys.argv:
    base    = "X { A {} B {} C {} }"
    derived = "Y : X { B DELETION; }"
elif "derived-3-end" in sys.argv:
    base    = "X { A {} B {} C {} }"
    derived = "Y : X { C DELETION; }"
elif "derived-2-begin" in sys.argv:
    base    = "X { A {} B {} }"
    derived = "Y : X { A DELETION; }"
elif "derived-2-end" in sys.argv:
    base    = "X { A {} B {} }"
    derived = "Y : X { B DELETION; }"
elif "derived-1" in sys.argv:
    base    = "X { A {} }"
    derived = "Y : X { A DELETION; }"
elif "derived-Nonsense" in sys.argv:
    base    = "X { A {} }"
    derived = "Y : X { Nonsense DELETION; }"
if   "before" in sys.argv:
    base = "X { A {} B {} C DELETION; C {} }"
if   "derived-before" in sys.argv:
    base = "X { A {} B {} C DELETION; }"
    derived = "Y : X { C {} }"

if derived is not None:
    test.do([base, derived], "DELETION")
else:
    test.do([base], "DELETION")


