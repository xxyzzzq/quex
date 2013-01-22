#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from StringIO import StringIO
import quex.input.regular_expression.engine        as regex
from   quex.engine.state_machine.core             import StateMachine
from   quex.engine.interval_handling              import NumberSet, Interval
import quex.engine.state_machine.utf16_state_split as trafo
from   quex.engine.state_machine.utf16_state_split import unicode_to_utf16
from   quex.engine.generator.base                 import get_combined_state_machine

if "--hwut-info" in sys.argv:
    print "UTF16 State Split: Larger Number Sets"


class X:
    def __init__(self, Name):
        sh = StringIO("[:\\P{Script=%s}:]" % Name)
        self.name = Name
        self.charset = charset_expression.snap_set_expression(sh, {})
        self.sm = StateMachine()
        self.sm.add_transition(self.sm.init_state_index, self.charset, AcceptanceF=True)
        self.id = self.sm.get_id()

    def check(self, SM):
        """This function throws an exception as soon as one single value
           is not matched according to the expectation.
        """
        print "Name = " + self.name, 
        for interval in self.charset.get_intervals(PromiseToTreatWellF=True):
            for i in range(interval.begin, interval.end):
                utf16_seq = unicode_to_utf16(i)

                # Apply sequence to state machine
                s_idx = result.init_state_index
                for word in utf16_seq:
                    s_idx = result.states[s_idx].transitions().get_resulting_target_state_index(word)

                assert s_idx is not None, \
                       "No acceptance for %X in [%X,%X] --> %s" % \
                       (i, interval.begin, interval.end - 1, repr(map(lambda x: "%04X." % x, utf16_seq)))

                # All acceptance flags must belong to the original state machine
                for origin in result.states[s_idx].origins():
                    if not origin.is_acceptance(): continue
                    # HERE: As soon as something is wrong --> fire an exception
                    assert origin.pattern_id() == self.id
        print " (OK=%i)" % self.id

def check_negative(SM, ImpossibleIntervals):
    """None of the given unicode values shall reach an acceptance state.
    """
    print "Inverse Union Check:",
    for interval in ImpossibleIntervals:
        for i in [interval.begin, (interval.end + interval.begin) / 2, interval.end - 1]:
            utf16_seq = unicode_to_utf16(i)

            # Apply sequence to state machine
            s_idx = result.init_state_index
            for word in utf16_seq:
                s_idx = result.states[s_idx].transitions().get_resulting_target_state_index(word)
                if s_idx is None: break
            if s_idx is None: continue

            # An acceptance state cannot be reached by a unicode value in ImpossibleIntervals
            for origin in result.states[s_idx].origins():
                assert not origin.is_acceptance()

    print " (OK)"

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
print "#   UTF8-Splitted: %i" % len(result.states)

# print result.get_graphviz_string(Option="hex")

for set in sets:
    set.check(result)

union = NumberSet()
for nset in map(lambda set: set.charset, sets):
    union.unite_with(nset)

inverse_union = NumberSet(Interval(0, 0x110000))
inverse_union.subtract(union)
# print inverse_union.get_string(Option="hex")
check_negative(result, inverse_union.get_intervals(PromiseToTreatWellF=True))

