#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner, \
                                                                       LinearStateWalker

if "--hwut-info" in sys.argv:
    print "Accumulation;"
    print "CHOICES: %s;" % get_sm_shape_names()
    sys.exit()

sm, state_n, pic = get_sm_shape_by_name(sys.argv[1])

print pic

sm.get_init_state().single_entry.add(get_SeAccept(4711L, 33L))

examiner        = Examiner(sm, RecipeAcceptance)
examiner.categorize()
springs         = examiner.setup_initial_springs()
mouth_ready_set = examiner._accumulate(springs)

def print_recipe(si, R):
    if R is None: 
        print "  %02i <void>" % si
    else:
        print "  %02i %s" % (si, str(R).replace("\n", "\n     "))

print "Mouths ready for interference:"
print "   %s" % sorted(list(mouth_ready_set))
print
print "Linear States:"
for si, info in examiner.linear_db.iteritems():
    print_recipe(si, info.recipe)

print "Mouth States:"
for si, info in examiner.mouth_db.iteritems():
    print_recipe(si, info.recipe)

