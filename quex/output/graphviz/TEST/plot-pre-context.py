#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.output.graphviz.core            as plotter
import quex.input.regular_expression.engine as regex
from   quex.engine.generator.action_info    import PatternActionInfo

if "--hwut-info" in sys.argv:
    print "Plot: Pre-Context."
    sys.exit(0)


sm = regex.do("[Hh]ello" "[Ww]orld/a((b+ee(fe)*)+(b+cd)?)/", {})
pattern_action_pair_list = [ PatternActionInfo(sm, "Don't worry, be happy!") ]

my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot", "fig")

my_plotter.do()

# HWUT consideres '##' as comment
print open(my_plotter.pre_context_file_name).read() # .replace("#", "##")
os.remove(my_plotter.pre_context_file_name)
os.remove("test-plot.fig")


