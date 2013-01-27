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
    print "Plot: Pre-Context."
    sys.exit(0)


sm  = regex.do("[Hh]ello" "[Ww]orld/a((b+ee(fe)*)+(b+cd)?)/", {})
pap = PatternActionInfo(sm, "Don't worry, be happy!")
pap.pattern().mount_pre_context_sm()
pattern_action_pair_list = [ pap ]

my_plotter = plotter.Generator(pattern_action_pair_list, "test-plot")

my_plotter.do()

# HWUT consideres '##' as comment
for line in open(my_plotter.pre_context_file_name).readlines(): # .replace("#", "##")
    if line.find("digraph") != -1:
        print "digraph state_machine {"
    else:
        print "%s" % line,
os.remove(my_plotter.pre_context_file_name)
os.remove("test-plot.dot")


