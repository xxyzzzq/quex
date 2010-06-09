#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from StringIO import StringIO
import quex.core_engine.regular_expression.core        as regex
from   quex.core_engine.state_machine.core             import StateMachine
from   quex.core_engine.interval_handling              import NumberSet, Interval
import quex.core_engine.state_machine.utf8_state_split as trafo
from   quex.core_engine.state_machine.utf8_state_split import unicode_to_utf8
import quex.core_engine.regular_expression.core        as regex
from   quex.core_engine.generator.base                 import get_combined_state_machine

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Larger Number Sets"


sm1 = regex.do("[ΆΈΉΊΌΎ-Ϋ]+", {})
sm2 = regex.do("[ \\t\\n]", {})
result = trafo.do(get_combined_state_machine([sm1, sm2]))
print result.get_graphviz_string(NormalizeF=True, Option="hex")
