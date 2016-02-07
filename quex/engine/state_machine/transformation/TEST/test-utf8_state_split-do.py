#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from StringIO import StringIO
import quex.input.regular_expression.engine        as regex
from   quex.engine.state_machine.core             import StateMachine
from   quex.engine.state_machine.state.single_entry import SeAccept     
from   quex.engine.misc.interval_handling              import NumberSet, Interval
import quex.engine.state_machine.transformation.utf8_state_split as trafo
from   quex.engine.state_machine.transformation.utf8_state_split import unicode_to_utf8
from   quex.engine.state_machine.engine_state_machine_set                 import get_combined_state_machine

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Larger Number Sets"
    sys.exit()


class X:
    def __init__(self, Name):
        sh = StringIO("[:\\P{Script=%s}:]" % Name)
        self.name = Name
        self.charset = regex.snap_set_expression(sh, {})
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
                utf8_seq = unicode_to_utf8(i)

                # Apply sequence to state machine
                s_idx = result.init_state_index
                for byte in utf8_seq:
                    s_idx = result.states[s_idx].target_map.get_resulting_target_state_index(byte)

                # All acceptance flags must belong to the original state machine
                if not any(cmd.acceptance_id() == self.id 
                           for cmd in state.single_entry.get_iterable(SeAccept)):
                    print 
                    print "#sm.orig:  ", self.sm.get_string(NormalizeF=False, Option="hex")
                    print "#sm.result:", SM.get_string(NormalizeF=False, Option="hex")
                    print "#UCS: { interval: %s; value: %s; }" % (interval.get_string(Option="hex"), i)
                    print "#Seq: ", ["0x%02X" % x for x in utf8_seq]
                    print "#expected:", self.id
                    print "#found:", cmd_list
                    assert False
        print " (OK=%i)" % self.id

def check_negative(SM, ImpossibleIntervals):
    """Non of the given unicode values shall reach an acceptance state.
    """
    print "Inverse Union Check:",
    for interval in ImpossibleIntervals:
        front  = interval.begin
        middle = (interval.end + interval.begin) / 2
        back   = interval.end - 1
        for i in [front, middle, back]:
            utf8_seq = unicode_to_utf8(i)

            # Apply sequence to state machine
            state = result.apply_sequence(utf8_seq)
            if state is None: continue

            # An acceptance state cannot be reached by a unicode value in ImpossibleIntervals
            assert not state.is_acceptance()

    print " (OK)"

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
    x.check(result)

union = NumberSet()
for x in sets:
    union.unite_with(x.charset)

inverse_union = NumberSet(Interval(0, 0x110000))
inverse_union.subtract(union)
# print inverse_union.get_string(Option="hex")
check_negative(result, inverse_union.get_intervals(PromiseToTreatWellF=True))
