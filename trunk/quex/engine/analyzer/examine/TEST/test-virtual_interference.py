#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine, State
from quex.engine.state_machine.state.single_entry               import SingleEntry
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.operations.se_operations                       import SeAccept
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.state_info                    import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner, \
                                                                       LinearStateWalker
from quex.blackboard import E_PreContextIDs
from copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Virtual Interference: Acceptance;"
    print "CHOICES: restore-all, sequence;"
    sys.exit()

def print_recipe(si, R, UndeterminedSet):
    if R is None: 
        print "  %02i <void> (ERROR!)" % si
    else:
        if UndeterminedSet is None:
            undetermined_str = "ALL(ERROR!)"
        else:
            undetermined_str = str(sorted(list(UndeterminedSet)))

        print "  %02i %s    Undetermined: %s" % (si, str(R).replace("\n", "\n     "), 
                                               undetermined_str)

def get_MouthStateInfo(AcceptanceScheme, SingleEntry):
    info   = MouthStateInfo(FromStateIndexSet=set([0L, 1L]))
    recipe_before = RecipeAcceptance(deepcopy(AcceptanceScheme), {})
    entry_recipe  = RecipeAcceptance.accumulate(recipe_before, SingleEntry)
    info.entry_recipe_db = {
        0: None,
        1: entry_recipe,
    }
    return info

def set_SingleEntry(sm, StateIndex, TheSingleEntry):
    sm.states[StateIndex] = State()
    sm.states[StateIndex].single_entry = TheSingleEntry

if "restore-all" in sys.argv:
    scheme = [ 
        RecipeAcceptance.RestoreAcceptance
    ]
else:
    scheme = [ 
        SeAccept(1111L, 11L, True), 
        SeAccept(2222L, 22L, True), 
        SeAccept(3333L, E_PreContextIDs.NONE, True) 
    ]

single_entry_1 = SingleEntry.from_iterable([])
single_entry_2 = SingleEntry.from_iterable([ SeAccept(4444L, E_PreContextIDs.NONE, False) ])
single_entry_3 = SingleEntry.from_iterable([ SeAccept(5555L, 55L, False) ])
single_entry_4 = SingleEntry.from_iterable([
    SeAccept(1111L, 11L, True), 
    SeAccept(2222L, 22L, True), 
])

sm = StateMachine()
# Empty 'op(i)'
print "State 1: Empty op(i)"
set_SingleEntry(sm, 1L, single_entry_1)

print "State 2: Overwriting op(i)"
set_SingleEntry(sm, 2L, single_entry_2)

print "State 3: Concatenating op(i)"
set_SingleEntry(sm, 3L, single_entry_3)

print "State 4: Concatenating longer op(i)"
set_SingleEntry(sm, 4L, single_entry_4)

examiner = Examiner(sm, DerivedRecipe)

# For the test, only 'examiner.mouth_db' and 'examiner.recipe_type'
# are important.

examiner.mouth_db[1L] = get_MouthStateInfo(scheme, single_entry_1)
examiner.mouth_db[2L] = get_MouthStateInfo(scheme, single_entry_2)
examiner.mouth_db[3L] = get_MouthStateInfo(scheme, single_entry_3)
examiner.mouth_db[4L] = get_MouthStateInfo(scheme, single_entry_4)

DerivedRecipe.position_register_by_state_db = {
    1L: [ 1111L, 2222L, 3333L, 4444L, 5555L ],
    2L: [ 1111L, 2222L, 3333L, 4444L, 5555L ],
    3L: [ 1111L, 2222L, 3333L, 4444L, 5555L ],
    4L: [ 1111L, 2222L, 3333L, 4444L, 5555L ],
}

examiner._interfere_virtually(set([1L, 2L, 3L, 4L]))

print "Mouth States After:"
for si, info in sorted(examiner.mouth_db.iteritems()):
    print_recipe(si, info.recipe, info.undetermined_register_set)
    print

