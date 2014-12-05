#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner

if "--hwut-info" in sys.argv:
    print "Categorize into Linear and Mouth States"
    print "CHOICES: linear, butterfly, long_loop, nested_loop, mini_loop, fork, fork2, fork3, fork4;"
    sys.exit()

sm = StateMachine(InitStateIndex=0L)

if   "linear"      in sys.argv: sm, state_n = get_linear(sm)
elif "butterfly"   in sys.argv: sm, state_n = get_butterfly(sm)
elif "long_loop"   in sys.argv: sm, state_n = get_long_loop(sm)
elif "nested_loop" in sys.argv: sm, state_n = get_nested_loop(sm)
elif "mini_loop"   in sys.argv: sm, state_n = get_mini_loop(sm)
elif "fork"        in sys.argv: sm, state_n = get_fork(sm)
elif "fork2"       in sys.argv: sm, state_n = get_fork2(sm)
elif "fork3"       in sys.argv: sm, state_n = get_fork3(sm)
else:                           sm, state_n = get_fork4(sm)

examiner = Examiner(sm, RecipeAcceptance)
examiner.categorize()

print "Linear States:", examiner.linear_db.keys()
print "Mouth  States:", examiner.mouth_db.keys()
