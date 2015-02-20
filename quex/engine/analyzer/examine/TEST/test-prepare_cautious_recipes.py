#! /usr/bin/env python
#
# PURPOSE: Test the production of a cautious recipe for acceptance considerations.
#
# Details on 'cautious recipes' see [DOC]. Brief: A cautious recipe is a recipe
# for a mouth state, that actually has undetermined entries. Thus, ordinary
# interference cannot be applied. Cautious recipes take the place of
# undetermined recipes. Since, then all entry recipes are defined, ordinary
# interference produces a correct recipe that assumes that values are stored at
# state entry.
#
# Components of the mouth state's 'op(i)' which are constant do not trigger a 
# 'store/restore' behavior. The component can be overtaken to the output recipe.
#
# Core Test: 
#
#    -- Setup mouth state with undetermined entries in '.entry_recipe_db'.
#
#    -- Setup 'op(i)' for the mouth state.
#
#    -- ._prepare_cautious_recipe()
#         => .entry_recipe_db[p] = cautious recipe
#            for all predecessor state indices 'p'.
#
#    -- ordinary interference
#         => A correct output recipe.
#______________________________________________________________________________
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

def setup_mouth_with_undetermined_entries(examiner, EntryN, SomeRecipe0, SomeRecipe1):
    EntryN = 4
    mouth  = MouthStateInfo(FromStateIndexSet=set(xrange(EntryN)))
    if EntryN > 0: mouth.entry_recipe_db[0] = None
    if EntryN > 1: mouth.entry_recipe_db[1] = SomeRecipe0
    if EntryN > 2: mouth.entry_recipe_db[2] = None
    if EntryN > 3: mouth.entry_recipe_db[3] = SomeRecipe1
    if EntryN > 4: mouth.entry_recipe_db[4] = None

    return mouth

def setup_state_operation(sm, CmdList):
    state_index = max(set(sm.states.iterkeys())) + 1
    state       = State()
    for cmd in CmdList:
        state.single_entry.add(cmd)
    sm.states[state_index] = state
    return state_index

def setup(EntryN, StateOperation):
    sm        = StateMachine()
    examiner  = Examiner(sm, RecipeAcceptance)

    si        = setup_state_operation(sm, StateOperation) 
    operation = sm.states[si].single_entry

    examiner.linear_db[sm.init_state_index] = LinearStateInfo()

    predecessor0_recipe  = RecipeAcceptance([SeAccept(0)], {si: 0}, {})
    recipe0              = examiner.recipe_type.accumulation(predecessor0_recipe, operation)
    predecessor1_recipe  = RecipeAcceptance([SeAccept(1)], {si: 0}, {})
    recipe1              = examiner.recipe_type.accumulation(predecessor1_recipe, operation)

    mouth    = setup_mouth_with_undetermined_entries(examiner, EntryN, recipe0, recipe1)
    examiner.mouth_db[si] = mouth

    examiner.determine_required_sets_of_variables()
    assert set(examiner.mouth_db).isdisjoint(examiner.linear_db), \
           "%s intersects with %s" % (set(examiner.mouth_db), set(examiner.linear_db))
    return examiner, si

def test(StateOperation):
    examiner, si = setup(5, StateOperation)
    examiner._prepare_cautious_recipe(si)
    examiner._interference([si])
    print_interference_result(examiner.mouth_db)

# test([])
# test([SeAccept(4711L)])
test([SeStoreInputPosition(4711L)])
