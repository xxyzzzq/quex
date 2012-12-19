#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
sys.path.insert(0, os.getcwd())

import match_precedence_test as test

if "--hwut-info" in sys.argv:
    print "Checking PRIORITY-MARK internally.;"
    print "CHOICES: 3-begin, 3-mid, 3-end, 2-begin, 2-end, 1, Nonsense," \
                   "derived-3-begin, derived-3-mid, derived-3-end, derived-2-begin, derived-2-end, derived-1, derived-Nonsense," \
                   "before, derived-before;"
    sys.exit()

def check(*TxtList):
    print "#---------------------------------------------------------------------------"
    for txt in TxtList:
        print "mode %s" % txt
    print
    test.do(TxtList, "PRIORITY")

if   "3-begin" in sys.argv:
    check("X { A {a} B {b} C {c} A PRIORITY-MARK; }")
    check("X { A {a} B {b}       A PRIORITY-MARK; C {c} }")
    check("X { A {a}             A PRIORITY-MARK; B {b} C {c} }")
    check("X {                   A PRIORITY-MARK; A {a} B {b} C {c} }")
elif "3-mid" in sys.argv:
    check("X { A {a} B {b} C {c} B PRIORITY-MARK; }")
    check("X { A {a} B {b}       B PRIORITY-MARK; C {c} }")
    check("X { A {a}             B PRIORITY-MARK; B {b} C {c} }")
    check("X {                   B PRIORITY-MARK; A {a} B {b} C {c} }")
elif "3-end" in sys.argv:
    check("X { A {a} B {b} C {c} C PRIORITY-MARK; }")
    check("X { A {a} B {b}       C PRIORITY-MARK; C {c} }")
    check("X { A {a}             C PRIORITY-MARK; B {b} C {c} }")
    check("X {                   C PRIORITY-MARK; A {a} B {b} C {c} }")
elif "2-begin" in sys.argv:
    check("X { A {a} B {b} A PRIORITY-MARK; }")
    check("X { A {a}       A PRIORITY-MARK; B {b} }")
    check("X {             A PRIORITY-MARK; A {a} B {b} }")
elif "2-end" in sys.argv:
    check("X { A {a} B {b} B PRIORITY-MARK; }")
    check("X { A {a}       B PRIORITY-MARK; B {b} }")
    check("X {             B PRIORITY-MARK; A {a} B {b} }")
elif "1" in sys.argv:
    check("X { A {a} A PRIORITY-MARK; }")
    check("X {       A PRIORITY-MARK; B {b} }")
elif "Nonsense" in sys.argv:
    check("X { A {a} Nonsense PRIORITY-MARK; }")
    check("X {       Nonsense PRIORITY-MARK; A {a} }")
elif   "derived-3-begin" in sys.argv:
    check("X { A {a} B {b} C {c} }", "Y : X {       A PRIORITY-MARK; }")
    check("X { A {a} B {b} C {c} }", "Y : X { D {d} A PRIORITY-MARK; }")
    check("X { A {a} B {b} C {c} }", "Y : X {       A PRIORITY-MARK; D {d} }")
    check("X { A {a} B {b} C {c} }", "Y : X { D {d} A PRIORITY-MARK; E {e} }")
elif "derived-3-mid" in sys.argv:
    check("X { A {a} B {b} C {c} }", "Y : X {       B PRIORITY-MARK; }")
    check("X { A {a} B {b} C {c} }", "Y : X { D {d} B PRIORITY-MARK; }")
    check("X { A {a} B {b} C {c} }", "Y : X {       B PRIORITY-MARK; D {d} }")
    check("X { A {a} B {b} C {c} }", "Y : X { D {d} B PRIORITY-MARK; E {e} }")
elif "derived-3-end" in sys.argv:
    check("X { A {a} B {b} C {c} }", "Y : X {       C PRIORITY-MARK; }")
    check("X { A {a} B {b} C {c} }", "Y : X { D {d} C PRIORITY-MARK; }")
    check("X { A {a} B {b} C {c} }", "Y : X {       C PRIORITY-MARK; D {d} }")
    check("X { A {a} B {b} C {c} }", "Y : X { D {d} C PRIORITY-MARK; E {e} }")
elif "derived-2-begin" in sys.argv:
    check("X { A {a} B {b} }", "Y : X {       A PRIORITY-MARK; }")
    sys.exit()
    check("X { A {a} B {b} }", "Y : X { D {d} A PRIORITY-MARK; }")
    check("X { A {a} B {b} }", "Y : X {       A PRIORITY-MARK; D {d} }")
    check("X { A {a} B {b} }", "Y : X { D {d} A PRIORITY-MARK; E {e} }")
elif "derived-2-end" in sys.argv:
    check("X { A {a} B {b} }", "Y : X {       B PRIORITY-MARK; }")
    check("X { A {a} B {b} }", "Y : X { D {d} B PRIORITY-MARK; }")
    check("X { A {a} B {b} }", "Y : X {       B PRIORITY-MARK; D {d} }")
    check("X { A {a} B {b} }", "Y : X { D {d} B PRIORITY-MARK; E {e} }")
elif "derived-1" in sys.argv:
    check("X { A {a} }", "Y : X {       A PRIORITY-MARK; }")
    check("X { A {a} }", "Y : X { D {d} A PRIORITY-MARK; }")
    check("X { A {a} }", "Y : X {       A PRIORITY-MARK; D {d} }")
    check("X { A {a} }", "Y : X { D {d} A PRIORITY-MARK; E {e} }")
elif "derived-Nonsense" in sys.argv:
    check("X { A {a} }", "Y : X {       Nonsense PRIORITY-MARK; }")
    check("X { A {a} }", "Y : X { D {d} Nonsense PRIORITY-MARK; }")
    check("X { A {a} }", "Y : X {       Nonsense PRIORITY-MARK; D {d} }")
    check("X { A {a} }", "Y : X { D {d} Nonsense PRIORITY-MARK; E {e} }")
if   "before" in sys.argv:
    check("X { A {a} B {b} C PRIORITY-MARK; C {c} }")
if   "derived-before" in sys.argv:
    check("X { A {a} B {b} C PRIORITY-MARK; }", "Y : X { C {c} }")


