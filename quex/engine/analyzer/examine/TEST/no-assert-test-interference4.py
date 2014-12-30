#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core                             import StateMachine
from quex.engine.operations.se_operations                       import SeAccept
from quex.engine.state_machine.TEST.helper_state_machine_shapes import *
from quex.engine.analyzer.examine.TEST.helper                   import *
from quex.engine.analyzer.examine.state_info                    import *
from quex.engine.analyzer.examine.acceptance                    import RecipeAcceptance
from quex.engine.analyzer.examine.core                          import Examiner, \
                                                                       LinearStateWalker
from quex.blackboard import E_PreContextIDs, E_R, E_IncidenceIDs
from copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Interference: Inhomogeneous IpOffset;"
    print "CHOICES: 2-entries, 3-entries;"
    print "SAME;"
    sys.exit()

choice  = sys.argv[1].split("-")
entry_n = int(choice[0])

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

def get_array(EntryN, IpOffsetDb):

    def get_entry(i, IpOffsetDb):
        """Let one entry be different."""
        result = deepcopy(IpOffsetDb)
        if i == 1:  # i = 1, always happens
            # always only take the last as different
            if len(result) == 0: result = { 0L: -1 }
            else:                result[len(result)-1] += 1000
        return result

    return [ 
        RecipeAcceptance([RecipeAcceptance.RestoreAcceptance], get_entry(i, IpOffsetDb)) 
        for i in xrange(EntryN) 
    ]

def get_MouthStateInfo(EntryN, IpOffsetDb):
    info  = MouthStateInfo(FromStateIndexSet=set(xrange(entry_n)))
    array = get_array(entry_n, IpOffsetDb)
    for i, recipe in enumerate(array):
        info.entry_recipe_db[i] = recipe
    return info

scheme_0 = {}
scheme_1 = { 0: -1 } 
scheme_2 = { 0: -1, 1: -2 }
scheme_3 = { 0: -1, 1: -2, 2: -3 }


examiner = Examiner(StateMachine(), DerivedRecipe)

# For the test, only 'examiner.mouth_db' and 'examiner.recipe_type'
# are important.
examiner.mouth_db[1L] = get_MouthStateInfo(entry_n, scheme_0)
examiner.mouth_db[2L] = get_MouthStateInfo(entry_n, scheme_1)
examiner.mouth_db[3L] = get_MouthStateInfo(entry_n, scheme_2)
examiner.mouth_db[4L] = get_MouthStateInfo(entry_n, scheme_3)

DerivedRecipe.position_register_by_state_db = {
    1L: [0],
    2L: [0],
    3L: [0, 1],
    4L: [0, 1, 2]
}
examiner._interfere(set([1L, 2L, 3L, 4L]))


print "Mouth States:"
for si, info in examiner.mouth_db.iteritems():
    print_recipe(si, info.recipe, info.undetermined_register_set)
    print

