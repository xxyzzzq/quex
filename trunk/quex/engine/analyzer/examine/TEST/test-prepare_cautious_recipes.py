#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.state_machine.state.core                       import State
from quex.engine.state_machine.state.single_entry               import SingleEntry
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner, \
                                                                       LinearStateWalker
from quex.blackboard import E_IncidenceIDs, E_PreContextIDs

if "--hwut-info" in sys.argv:
    print "Prepare Cautious Recipes;"
    sys.exit()

# choice = sys.argv[1]

def setup_mouth(examiner, StateIndex, EntryN, SomeRecipe0, SomeRecipe1):
    EntryN = 4
    mouth  = MouthStateInfo(FromStateIndexSet=set(xrange(EntryN)))
    if EntryN > 0: mouth.entry_recipe_db[0] = None
    if EntryN > 1: mouth.entry_recipe_db[1] = SomeRecipe0
    if EntryN > 2: mouth.entry_recipe_db[2] = None
    if EntryN > 3: mouth.entry_recipe_db[3] = SomeRecipe1
    if EntryN > 4: mouth.entry_recipe_db[4] = None

    examiner.mouth_db[StateIndex] = mouth

def setup_state(sm, *OperationList):
    state_index = long(len(sm.states))
    sm.states[state_index] = State(SingleEntry.from_iterable(OperationList))
    return state_index

def setup(examiner, sm, EntryN):
    si       = setup_state(sm) #, SeAccept(4711L)) 
    examiner.linear_db[sm.init_state_index] = LinearStateInfo()

    recipe0  = RecipeAcceptance([SeAccept(0)], {si: 0}, {})
    recipe1  = RecipeAcceptance([SeAccept(1)], {si: 0}, {})

    setup_mouth(examiner, si, EntryN, recipe0, recipe1)

sm       = StateMachine()
examiner = Examiner(sm, RecipeAcceptance)

setup(examiner, sm, 5)

examiner.determine_required_sets_of_variables()

examiner._prepare_cautious_recipe(1L)
examiner._interference([1L])
print_interference_result(examiner.mouth_db)
