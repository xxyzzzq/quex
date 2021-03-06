#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.operations.se_operations                       import SeAccept
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner
from quex.blackboard import E_IncidenceIDs

if "--hwut-info" in sys.argv:
    print "Accumulation;"
    print "CHOICES: %s;" % get_sm_shape_names()
    sys.exit()

sm, state_n, pic = get_sm_shape_by_name(sys.argv[1])

print pic

sm.get_init_state().single_entry.add(SeAccept(4711L, 33L))
# sm.get_init_state().single_entry.add(SeAccept(E_IncidenceIDs.MATCH_FAILURE))

examiner        = Examiner(sm, RecipeAcceptance)
examiner.categorize()
springs         = examiner.setup_initial_springs()
mouth_ready_set = examiner._accumulate(springs)

print "Mouths ready for interference:"
print "   %s" % sorted(list(mouth_ready_set))
print
print "Linear States:"
for si, info in sorted(examiner.linear_db.iteritems()):
    print_recipe(si, info.recipe)

print "Mouth States:"
for si, info in sorted(examiner.mouth_db.iteritems()):
    print_recipe(si, info.recipe)
    for predecessor_si, entry_recipe in info.entry_recipe_db.iteritems():
        print "  from %s:" % predecessor_si
        print entry_recipe

