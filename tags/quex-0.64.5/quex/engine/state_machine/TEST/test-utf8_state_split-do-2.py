#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine        as regex
from   quex.engine.interval_handling               import NumberSet, Interval
import quex.engine.state_machine.utf8_state_split  as trafo
from   quex.engine.state_machine.utf8_state_split  import unicode_to_utf8
import quex.input.regular_expression.engine        as regex
from   quex.engine.generator.base                  import get_combined_state_machine

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Larger Number Sets"


sm1 = regex.do("[ΆΈΉΊΌΎ-Ϋ]+", {}).sm
sm2 = regex.do("[ \\t\\n]", {}).sm
result = trafo.do(get_combined_state_machine([sm1, sm2]))
for line in result.get_graphviz_string(NormalizeF=True, Option="hex").split("\n"):
    if line.find("digraph") != -1:
        print "digraph state_machine {"
    else:
        print line
