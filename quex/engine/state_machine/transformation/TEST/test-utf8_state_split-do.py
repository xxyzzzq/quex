#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from StringIO import StringIO
import quex.input.regular_expression.engine                      as     regex
from   quex.engine.state_machine.core                            import StateMachine
from   quex.engine.state_machine.state.single_entry              import SeAccept     
from   quex.engine.misc.interval_handling                        import NumberSet, Interval
import quex.engine.state_machine.transformation.utf8_state_split as     trafo
from   quex.engine.state_machine.transformation.utf8_state_split import unicode_to_utf8
from   quex.engine.state_machine.engine_state_machine_set        import get_combined_state_machine
from   quex.engine.state_machine.transformation.TEST.helper      import X, check_negative

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Larger Number Sets"
    sys.exit()

sets = [ X(name)
         for name in ["Arabic", "Armenian", "Balinese", "Bengali", "Bopomofo", "Braille",
                      "Hanunoo", "Hebrew", "Hiragana", "Inherited", "Kannada",
                      "Katakana", "Kharoshthi", "Khmer", "Lao", "Latin", "Limbu", "Linear_B", "Malayalam",
                      "Mongolian", "Myanmar", "New_Tai_Lue", "Nko", "Ogham", "Old_Italic", "Old_Persian",
                      "Syriac", "Tagalog", "Tagbanwa", "Tai_Le", "Tamil", "Telugu", "Thaana", "Thai",
                      "Tibetan", "Tifinagh", "Ugaritic", "Yi"]
]

orig = get_combined_state_machine([x.sm for x in sets])
print "Number of states in state machine:"
print "   Unicode:       %i" % len(orig.states)
result = trafo.do(orig)
print "   UTF8-Splitted: %i" % len(result.states)

for x in sets:
    x.check(result, unicode_to_utf8)

union = NumberSet()
for x in sets:
    union.unite_with(x.charset)

inverse_union = NumberSet(Interval(0, 0x110000))
inverse_union.subtract(union)
# print inverse_union.get_string(Option="hex")
check_negative(result, inverse_union.get_intervals(PromiseToTreatWellF=True), 
               unicode_to_utf8)
