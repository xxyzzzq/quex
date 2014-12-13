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

sm, state_n, pic = get_sm_shape_by_name(sys.argv[1])

examiner = Examiner(sm, RecipeAcceptance)
examiner.categorize()

print "Linear States:", examiner.linear_db.keys()
print "Mouth  States:", examiner.mouth_db.keys()
