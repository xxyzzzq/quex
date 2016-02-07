#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from StringIO import StringIO
from   quex.engine.misc.interval_handling                         import NumberSet, Interval
import quex.engine.state_machine.transformation.utf16_state_split as     trafo
from   quex.engine.state_machine.transformation.utf16_state_split import unicode_to_utf16
from   quex.engine.state_machine.engine_state_machine_set         import get_combined_state_machine
from   quex.engine.state_machine.transformation.TEST.helper       import X, check_negative

if "--hwut-info" in sys.argv:
    print "UTF16 State Split: Larger Number Sets"
    sys.exit()

sets = map(lambda name: X(name),
           [ "Arabic", "Armenian", "Balinese", "Bengali", "Bopomofo",
             "Braille", "Common",  "Cuneiform",  "Cypriot",  "Deseret",
             "Gothic",  "Greek",  
             "Han",  
             "Inherited",  "Kharoshthi",
             "Linear_B",  "Old_Italic",  "Old_Persian",  "Osmanya",
             "Phoenician",  "Shavian",  "Ugaritic", "Buginese", "Buhid",
             "Canadian_Aboriginal", "Cherokee", "Syloti_Nagri", "Syriac",
             "Tagalog", "Tagbanwa", "Tai_Le", "Yi", 
             ])

orig = get_combined_state_machine(map(lambda x: x.sm, sets))
print "# Number of states in state machine:"
print "#   Unicode:       %i" % len(orig.states)
result = trafo.do(orig)
print "#   UTF16-Splitted: %i" % len(result.states)

# print result.get_graphviz_string(Option="hex")

for set in sets:
    set.check(result, unicode_to_utf16)

union = NumberSet()
for nset in map(lambda set: set.charset, sets):
    union.unite_with(nset)

inverse_union = NumberSet(Interval(0, 0x110000))
inverse_union.subtract(union)
# print inverse_union.get_string(Option="hex")
check_negative(result, inverse_union.get_intervals(PromiseToTreatWellF=True), 
               unicode_to_utf16)

