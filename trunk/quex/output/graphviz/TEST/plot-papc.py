#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.output.graphviz.core               as plotter
import quex.input.regular_expression.engine    as regex
from   quex.input.regular_expression.construct import Pattern 
from   quex.input.files.mode                   import PatternActionInfo
from   quex.output.core.code.base         import CodeFragment

from   quex.blackboard import setup as Setup
Setup.normalize_f = True

if "--hwut-info" in sys.argv:
    print "Plot: Backward Detector (for pseudo-ambiguous post context)."
    sys.exit(0)

pattern = regex.do("a(((b+ee(fe)*)+(b+cd)?)|(b+cd))/bbb(cb)*(eebc)?de", {})
pattern.mount_post_context_sm()

pattern_list = [ 
    pattern
]

my_plotter = plotter.Generator(pattern_list, "test-plot")

my_plotter.do()

# HWUT consideres '##' as comment
for line in open(my_plotter.backward_detector_file_name[0]).readlines(): # .replace("#", "##")
    if line.find("digraph") != -1:
        print "digraph state_machine {"
    else:
        print "%s" % line,

os.remove("test-plot.dot")
os.remove(my_plotter.backward_detector_file_name[0])


