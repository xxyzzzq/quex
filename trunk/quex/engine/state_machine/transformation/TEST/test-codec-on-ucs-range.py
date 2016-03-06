#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.state_machine.transformation.core        as     bc_factory
from   quex.engine.state_machine.transformation.TEST.helper import test_on_UCS_range
from   quex.engine.misc.interval_handling                   import Interval

from   quex.blackboard import setup as Setup, E_IncidenceIDs

if "--hwut-info" in sys.argv:
    print "Table-Based Transformations (fixed size): Examplary Unicode Ranges"
    print "CHOICES: ascii, EBCDIC-CP-BE, arabic, cp037, cp1140, hebrew, iso8859_10, macgreek;"

    sys.exit()

encoding_name = sys.argv[1]
trafo = bc_factory.do(encoding_name)

SourceInterval = Interval(0, 0x100)
DrainInterval  = Interval(0, 0x100)

def transform_forward(X):
    global trafo
    interval          = Interval(X, X+1)
    verdict_f, result = interval.transform_by_table(trafo)
    if not verdict_f: return None
    assert len(result) == 1
    return result[0].begin

backward_db    = dict(
    (transform_forward(x), x)
    for x in range(SourceInterval.begin, SourceInterval.end)
    if transform_forward(x) is not None
)
def transform_backward(Y):
    global backward_db
    return backward_db.get(Y)

test_on_UCS_range(trafo, SourceInterval, DrainInterval, transform_backward)

