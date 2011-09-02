#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.command_line.query        as query
import quex.output.graphviz.core            as plotter
import quex.input.regular_expression.engine as regex
from   quex.engine.generator.action_info    import PatternActionInfo

if "--hwut-info" in sys.argv:
    print "Plot: Backward Detector (for pseudo-ambiguous post context)."
    sys.exit(0)


sm = regex.do("a(((b+ee(fe)*)+(b+cd)?)|(b+cd))/bbb(cb)*(eebc)?de", {})
pattern_action_pair_list = [ PatternActionInfo(sm, "Don't worry, be happy!") ]

my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot")

my_plotter.do()

# HWUT consideres '##' as comment
print open(my_plotter.backward_detector_file_name[0]).read() # .replace("#", "##")
os.remove("test-plot.dot")
os.remove(my_plotter.backward_detector_file_name[0])


