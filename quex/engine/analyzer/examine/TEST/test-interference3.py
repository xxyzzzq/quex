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
    print "Interference: Homogeneous IpOffset;"
    print "CHOICES: 2-entries, 3-entries;"
    print "SAME;"
    sys.exit()

choice  = sys.argv[1].split("-")
entry_n = int(choice[0])

scheme_0 = {}
scheme_1 = { 0: -1 } 
scheme_2 = { 0: -1, 1: -2 }
scheme_3 = { 0: -1, 1: -2, 2: -3 }


examiner = Examiner(StateMachine(), RecipeAcceptance)

# For the test, only 'examiner.mouth_db' and 'examiner.recipe_type'
# are important.
examiner.mouth_db[1L] = get_MouthStateInfoIpOffset(entry_n, scheme_0)
examiner.mouth_db[2L] = get_MouthStateInfoIpOffset(entry_n, scheme_1)
examiner.mouth_db[3L] = get_MouthStateInfoIpOffset(entry_n, scheme_2)
examiner.mouth_db[4L] = get_MouthStateInfoIpOffset(entry_n, scheme_3)

examiner._interference(set([1L, 2L, 3L, 4L]))

print_interference_result(examiner.mouth_db)

