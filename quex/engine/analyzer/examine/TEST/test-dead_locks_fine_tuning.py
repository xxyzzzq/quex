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
    print "Dead Locks: Fine Tuning;"
    print "CHOICES: butterfly, long_loop, nested_loop, mini_loop, fork, fork2, fork4;"
    sys.exit()

name             = sys.argv[1]
sm, state_n, pic = get_sm_shape_by_name(name)

print pic

add_SeAccept(sm, sm.init_state_index, E_IncidenceIDs.MATCH_FAILURE)
add_SeStoreInputPosition(sm, 1L, 77L)
if state_n > 3:    add_SeAccept(sm, 3L, 33L, 333L)
if state_n > 3:    add_SeAccept(sm, 4L, 44L)
if state_n > 3:    add_SeAccept(sm, 3L, 33L, 333L)
if state_n > 6:    add_SeAccept(sm, 6L, 66L, 666L)
# Post-Context: Store in '1', restore in '7'
if state_n > 7:    add_SeAccept(sm, 7L, 77L, E_PreContextIDs.NONE, True)

print

linear_db, mouth_db = examination.do(sm, RecipeAcceptance)

def print_recipe(si, R):
    if R is None: 
        print "  %02i <void>" % (si)
    else:
        print "  %02i %s" % (si, str(R).replace("\n", "\n     "))

def print_entry_recipe_db(si, EntryRecipeDb):
    print "  %02i\n" % si
    for from_si, recipe in sorted(EntryRecipeDb.iteritems()):
        if recipe is None: 
            print "  from %02s <void>" % from_si
        else:
            print "  from %02s \n     %s" % (from_si, str(recipe).replace("\n", "\n     "))

print "Linear States:"
for si, info in linear_db.iteritems():
    print_recipe(si, info.recipe)

print "Mouth States (Resolved):"
for si, info in mouth_db.iteritems():
    print_recipe(si, info.recipe)

