#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner
from quex.blackboard import E_IncidenceIDs, E_PreContextIDs

if "--hwut-info" in sys.argv:
    print "Resolve Without Dead-Lock Resolution;"
    print "CHOICES: %s;" % get_sm_shape_names()
    sys.exit()

name             = sys.argv[1]
sm, state_n, pic = get_sm_shape_by_name(name)

print pic

# add_SeAccept(sm, sm.init_state_index, E_IncidenceIDs.MATCH_FAILURE)
add_SeStoreInputPosition(sm, 1L, 77L)
add_SeAccept(sm, 1L, 1L, 111L)
add_SeAccept(sm, 3L, 33L, 333L)
add_SeAccept(sm, 4L, 44L)
add_SeAccept(sm, 6L, 66L, 666L)
# Post-Context: Store in '1', restore in '7'
add_SeAccept(sm, 7L, 77L, E_PreContextIDs.NONE, True)
print

examiner        = Examiner(sm, RecipeAcceptance)
examiner.categorize()
springs         = examiner.setup_initial_springs()
remainder       = examiner.resolve(springs)

print "Unresolved Mouth States:"
print "   %s" % sorted(list(remainder))
print
print "Linear States:"
for si, info in examiner.linear_db.iteritems():
    print_recipe(si, info.recipe)

print "Mouth States (Resolved):"
for si, info in examiner.mouth_db.iteritems():
    if si in remainder: continue
    print_recipe(si, info.recipe)

print "Mouth States (Unresolved):"
for si, info in examiner.mouth_db.iteritems():
    if si not in remainder: continue
    print_entry_recipe_db(si, info.entry_recipe_db)

print
print "Horizon:", sorted(list(examiner.get_horizon(examiner.mouth_db.keys())))
