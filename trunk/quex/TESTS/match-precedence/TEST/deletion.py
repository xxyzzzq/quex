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
                   "before, derived-before, derived-deeply, superset, subset;"
    sys.exit()

derived = None
if   "3-begin" in sys.argv:
    base = "X { A {a} B {b} C {c} A DELETION; }"
elif "3-mid" in sys.argv:
    base = "X { A {a} B {b} C {c} B DELETION; }"
elif "3-end" in sys.argv:
    base = "X { A {a} B {b} C {c} C DELETION; }"
elif "2-begin" in sys.argv:
    base = "X { A {a} B {b} A DELETION; }"
elif "2-end" in sys.argv:
    base = "X { A {a} B {b} B DELETION; }"
elif "1" in sys.argv:
    base = "X { A {a} A DELETION; }"
elif "Nonsense" in sys.argv:
    base = "X { A {a} Nonsense DELETION; }"
elif   "derived-3-begin" in sys.argv:
    base    = "X { A {a} B {b} C {c} }"
    derived = "Y : X { A DELETION; }"
elif "derived-3-mid" in sys.argv:
    base    = "X { A {a} B {b} C {c} }"
    derived = "Y : X { B DELETION; }"
elif "derived-3-end" in sys.argv:
    base    = "X { A {a} B {b} C {c} }"
    derived = "Y : X { C DELETION; }"
elif "derived-2-begin" in sys.argv:
    base    = "X { A {a} B {b} }"
    derived = "Y : X { A DELETION; }"
elif "derived-2-end" in sys.argv:
    base    = "X { A {a} B {b} }"
    derived = "Y : X { B DELETION; }"
elif "derived-1" in sys.argv:
    base    = "X { A {a} }"
    derived = "Y : X { A DELETION; }"
elif "derived-Nonsense" in sys.argv:
    base    = "X { A {a} }"
    derived = "Y : X { Nonsense DELETION; }"
elif "before" in sys.argv:
    base    = "X { A {a} B {b} C DELETION; C {c} }"
elif "derived-before" in sys.argv:
    base    = "X { A {a} B {b} C DELETION; }"
    derived = "Y : X { C {c} }"
elif "derived-deeply" in sys.argv:
    test.do(["X0 { A0 {a0} }", 
             "X1 : X0 { A1 {a1} }",
             "X2 : X1 { A2 {a2} }",
             "X3 : X2 { A3 {a3} }",
             "X  : X3 { A0 DELETION; }"], "DELETION")
    sys.exit(0)
elif "superset" in sys.argv:
    base    = "X { A+ {a}        0 {b} [A-Za-z]+ DELETION; }"
elif "subset" in sys.argv:
    base    = "X { [A-Za-z]+ {a} 0 {b} A+        DELETION; }"

if derived is not None:
    test.do([base, derived], "DELETION")
else:
    test.do([base], "DELETION")


