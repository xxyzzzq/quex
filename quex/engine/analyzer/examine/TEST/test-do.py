#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
import quex.engine.analyzer.examine.core                        as     examination
from quex.blackboard import E_IncidenceIDs, E_PreContextIDs

if "--hwut-info" in sys.argv:
    print "Complete Process;"
    print "CHOICES: %s;" % get_sm_shape_names()
    sys.exit()

name             = sys.argv[1]
sm, state_n, pic = get_sm_shape_by_name(name)

print pic

add_SeStoreInputPosition(sm, sm.init_state_index, 66L)
add_SeStoreInputPosition(sm, 1L, 77L)
add_SeAccept(sm, 1L, 11L, 111L)
add_SeAccept(sm, 2L, 22L, 222L)
add_SeAccept(sm, 3L, 33L)
add_SeAccept(sm, 4L, 44L)
add_SeAccept(sm, 5L, 55L)
# Post-Context: Store in '0', restore in '6'
add_SeAccept(sm, 6L, 66L, 666L, True)
# Post-Context: Store in '1', restore in '7'
add_SeAccept(sm, 7L, 77L, E_PreContextIDs.NONE, True)
print

linear_db, mouth_db = examination.do(sm, RecipeAcceptance)
all_set = set(linear_db.iterkeys())
all_set.update(mouth_db.iterkeys())

print "All states present in 'sm' are either linear states or mouth states? ",
print all_set == set(sm.states.iterkeys())
print "There are no undetermined mouth states? ",
print len([x for x in mouth_db.itervalues() if x.recipe is None]) == 0
print "There are no undetermined entry recipes into mouth states? ",
for mouth in mouth_db.itervalues():
    for recipe in mouth.entry_recipe_db.itervalues():
        if recipe is None: 
            print False 
            break
else:
    print True

print "Linear States: ",
print sorted(linear_db.keys())
print "Mouth States: ",
print sorted(mouth_db.keys())
print
print
print "Linear States:"
for si, info in linear_db.iteritems():
    print_recipe(si, info.recipe)

# print "Mouth States:"
print_interference_result(mouth_db)

