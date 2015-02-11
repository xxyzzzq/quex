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

def get_array(EntryN, AcceptanceScheme):
    return [ 
        RecipeAcceptance(deepcopy(AcceptanceScheme), {}, {}) 
        for i in xrange(EntryN) 
    ]

def get_MouthStateInfo(EntryN, AcceptanceScheme):
    info  = MouthStateInfo(FromStateIndexSet=set(xrange(entry_n)))
    array = get_array(entry_n, AcceptanceScheme)
    for i, recipe in enumerate(array):
        info.entry_recipe_db[i] = recipe
        info.required_variable_set = set([E_R.AcceptanceRegister])
    return info

scheme_restore  = [ 
    RecipeAcceptance.RestoreAcceptance 
]
scheme_simple   = [ 
    SeAccept(1111L, E_PreContextIDs.NONE, False) 
]
scheme_simple2  = [ 
    SeAccept(2222L, E_PreContextIDs.NONE, True) 
]
scheme_list     = [ 
    SeAccept(3333L, 33L, True), 
    SeAccept(4444L, 44L, True), 
    SeAccept(5555L, E_PreContextIDs.NONE, True) 
]

examiner = Examiner(StateMachine(), RecipeAcceptance)
examiner.categorize()
examiner.setup_initial_springs()

# For the test, only 'examiner.mouth_db' and 'examiner.recipe_type'
# are important.
examiner.mouth_db[1L] = get_MouthStateInfo(entry_n, scheme_restore)
examiner.mouth_db[2L] = get_MouthStateInfo(entry_n, scheme_simple)
examiner.mouth_db[3L] = get_MouthStateInfo(entry_n, scheme_simple2)
examiner.mouth_db[4L] = get_MouthStateInfo(entry_n, scheme_list)

examiner._interference(set([1L, 2L, 3L, 4L]))

print_interference_result(examiner.mouth_db)

