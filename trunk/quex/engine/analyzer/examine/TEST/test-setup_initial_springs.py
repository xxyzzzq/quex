#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner

if "--hwut-info" in sys.argv:
    print "Setup Initial Spring States;"
    print "CHOICES: linear, long_loop;"
    sys.exit()

sm, state_n, pic = get_sm_shape_by_name(sys.argv[1])

examiner = Examiner(sm, RecipeAcceptance)
examiner.categorize()

for si in examiner.setup_initial_springs():
    print "Spring: %i;" % si
    print "Recipe: {\n%s\n}" % str(examiner.get_state_info(si).recipe)

print "Linear States:"
for si, info in examiner.linear_db.iteritems():
    print "   %02i: determined: %s" % (si, info.recipe is not None)

print "Mouth States:"
for si, info in examiner.mouth_db.iteritems():
    print "   %02i: determined: %s" % (si, info.recipe is not None)
