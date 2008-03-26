#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.query as query
import quex.output.graphviz.interface as plotter
import quex.core_engine.regular_expression.core as regex
from   quex.core_engine.generator.action_info   import ActionInfo



if "--hwut-info" in sys.argv:
    print "Plot: Core state machine."
    sys.exit(0)


sm = regex.do("a(((b+ee(fe)*)+(b+cd)?)|(b+cd))")
pattern_action_pair_list = [ ActionInfo(sm, "Don't worry, be happy!") ]

my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot", "fig")

my_plotter.do()
content = open("test-plot.fig").read()
for line in content.split("\n"):
    if len(line) >= 1 and line[0] != "#": print line
os.remove("test-plot.fig")



