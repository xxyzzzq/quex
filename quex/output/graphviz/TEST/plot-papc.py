#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.output.graphviz.core            as plotter
import quex.input.regular_expression.engine as regex
from   quex.engine.generator.action_info    import PatternActionInfo

from   quex.blackboard import setup as Setup
Setup.normalize_f = True

if "--hwut-info" in sys.argv:
    print "Plot: Backward Detector (for pseudo-ambiguous post context)."
    sys.exit(0)


sm = regex.do("a(((b+ee(fe)*)+(b+cd)?)|(b+cd))/bbb(cb)*(eebc)?de", {})
pap = PatternActionInfo(sm, "Don't worry, be happy!")
pap.pattern().mount_post_context_sm()
pattern_action_pair_list = [ pap ]

my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot")

my_plotter.do()

# HWUT consideres '##' as comment
for line in open(my_plotter.backward_detector_file_name[0]).readlines(): # .replace("#", "##")
    if line.find("digraph") != -1:
        print "digraph state_machine {"
    else:
        print "%s" % line,

os.remove("test-plot.dot")
os.remove(my_plotter.backward_detector_file_name[0])


