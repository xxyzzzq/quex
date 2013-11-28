#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.output.graphviz.core            as plotter
import quex.input.regular_expression.engine as regex
from   quex.engine.generator.code.core      import PatternActionInfo
from   quex.blackboard import setup as Setup
Setup.normalize_f = True

if "--hwut-info" in sys.argv:
    print "Plot: Core state machine."
    sys.exit(0)


sm = regex.do("a(((b+ee(fe)*)+(b+cd)?)|(b+cd))", {})
pattern_action_pair_list = [ PatternActionInfo(sm, "Don't worry, be happy!") ]

# HWUT consideres '##' as comment
my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot")

my_plotter.do()
for line in open("test-plot.dot").readlines(): # .replace("#", "##")
    if line.find("digraph") != -1:
        print "digraph state_machine {"
    else:
        print "%s" % line,
os.remove("test-plot.dot")



