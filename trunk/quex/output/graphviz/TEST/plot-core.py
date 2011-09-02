#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.query        as query
import quex.output.graphviz.core            as plotter
import quex.input.regular_expression.engine as regex
from   quex.engine.generator.action_info    import PatternActionInfo



if "--hwut-info" in sys.argv:
    print "Plot: Core state machine."
    sys.exit(0)


sm = regex.do("a(((b+ee(fe)*)+(b+cd)?)|(b+cd))", {})
pattern_action_pair_list = [ PatternActionInfo(sm, "Don't worry, be happy!") ]

# HWUT consideres '##' as comment
my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot")

my_plotter.do()
print open("test-plot.dot").read() # .replace("#", "##")
os.remove("test-plot.dot")



