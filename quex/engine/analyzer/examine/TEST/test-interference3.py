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
from quex.blackboard import E_PreContextIDs
from copy import deepcopy

if "--hwut-info" in sys.argv:
    print "Interference: Homogeneous Acceptance;"
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

def get_array(EntryN, AcceptanceScheme):
    def get_entry(i, AcceptanceScheme):
        """Let one entry be different."""
        result = deepcopy(AcceptanceScheme)
        if i == 1:  # i = 1, always happens
            # always only take the last as different
            if result is None: result = [ 100000 ]
            else:              result[len(result)-1] = 100000
        return result

    return [ 
        RecipeAcceptance(get_entry(i, AcceptanceScheme), {}) 
        for i in xrange(EntryN) 
    ]


def get_MouthStateInfo(EntryN, AcceptanceScheme):
    info  = MouthStateInfo(FromStateIndexSet=set(xrange(entry_n)))
    array = get_array(entry_n, AcceptanceScheme)
    for i, recipe in enumerate(array):
        info.entry_recipe_db[i] = recipe
    return info

scheme_restore  = None
scheme_simple   = [ get_SeAccept(1111L, E_PreContextIDs.NONE, False) ]
scheme_simple2  = [ get_SeAccept(2222L, 22L,                  True) ]
scheme_list     = [ 
    get_SeAccept(3333L, 33L, True), 
    get_SeAccept(4444L, 44L, True), 
    get_SeAccept(5555L, E_PreContextIDs.NONE, True) 
]

examiner = Examiner(StateMachine(), RecipeAcceptance)
# For the test, only 'examiner.mouth_db' and 'examiner.recipe_type'
# are important.
examiner.mouth_db[1L] = get_MouthStateInfo(entry_n, scheme_restore)
examiner.mouth_db[2L] = get_MouthStateInfo(entry_n, scheme_simple)
examiner.mouth_db[3L] = get_MouthStateInfo(entry_n, scheme_simple2)
examiner.mouth_db[4L] = get_MouthStateInfo(entry_n, scheme_list)

examiner._interfere(set([1L, 2L, 3L, 4L]))

print "Mouth States:"
for si, info in examiner.mouth_db.iteritems():
    print_recipe(si, info.recipe, info.undetermined_register_set)
    print

