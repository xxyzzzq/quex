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
    print "Interference: Inhomogeneous Acceptance;"
    print "CHOICES: 2-entries, 3-entries;"
    print "SAME;"
    sys.exit()

choice  = sys.argv[1].split("-")
entry_n = int(choice[0])

scheme_restore  = [ 
    RecipeAcceptance.RestoreAcceptance 
]
scheme_simple   = [ 
    get_SeAccept(1111L, E_PreContextIDs.NONE, False) 
]
scheme_simple2  = [ 
    get_SeAccept(2222L, 22L,                  True) 
]
scheme_list     = [ 
    get_SeAccept(3333L, 33L, True), 
    get_SeAccept(4444L, 44L, True), 
    get_SeAccept(5555L, E_PreContextIDs.NONE, True) 
]

examiner = Examiner(StateMachine(), RecipeAcceptance)
# For the test, only 'examiner.mouth_db' and 'examiner.recipe_type'
# are important.
examiner.mouth_db[1L] = get_MouthStateInfoAcceptance(entry_n, scheme_restore, False)
examiner.mouth_db[2L] = get_MouthStateInfoAcceptance(entry_n, scheme_simple, False)
examiner.mouth_db[3L] = get_MouthStateInfoAcceptance(entry_n, scheme_simple2, False)
examiner.mouth_db[4L] = get_MouthStateInfoAcceptance(entry_n, scheme_list, False)

examiner._interference(set([1L, 2L, 3L, 4L]))

print_interference_result(examiner.mouth_db)
