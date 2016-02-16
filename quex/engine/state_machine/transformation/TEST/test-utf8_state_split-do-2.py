#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine                      as regex
from   quex.engine.misc.interval_handling                        import NumberSet, Interval
from   quex.engine.state_machine.transformation.utf8_state_split import EncodingTrafoUTF8
import quex.input.regular_expression.engine                      as regex
from   quex.engine.state_machine.engine_state_machine_set        import get_combined_state_machine
import quex.engine.state_machine.algorithm.beautifier     as     beautifier

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Larger Number Sets"
    sys.exit()


sm1 = regex.do("[ΆΈΉΊΌΎ-Ϋ]+", {}).sm
sm2 = regex.do("[ \\t\\n]", {}).sm
verdict_f, result = EncodingTrafoUTF8().do_state_machine(get_combined_state_machine([sm1, sm2]), beautifier)
for line in result.get_graphviz_string(NormalizeF=True, Option="hex").splitlines():
    if line.find("digraph") != -1:
        print "digraph state_machine {"
    else:
        print line
