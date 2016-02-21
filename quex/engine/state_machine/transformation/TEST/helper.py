import quex.input.regular_expression.engine               as     regex
from   quex.engine.misc.interval_handling                 import NumberSet, Interval
from   quex.engine.state_machine.state.single_entry       import SeAccept     
from   quex.engine.state_machine.engine_state_machine_set import get_combined_state_machine
import quex.engine.state_machine.algorithm.beautifier     as     beautifier
from   quex.engine.state_machine.core                     import StateMachine
from   StringIO import StringIO
import sys

class X:
    def __init__(self, Name):
        sh = StringIO("[:\\P{Script=%s}:]" % Name)
        self.name = Name
        self.charset = regex.snap_set_expression(sh, {})
        self.sm = StateMachine()
        self.sm.add_transition(self.sm.init_state_index, self.charset, AcceptanceF=True)
        self.id = self.sm.get_id()

    def check(self, SM, TransformFunc):
        """This function throws an exception as soon as one single value
           is not matched according to the expectation.
        """
        print "## [%i] Name = %s" % (self.id, self.name), 
        interval_list  = self.charset.get_intervals(PromiseToTreatWellF=True)
        interval_count = len(interval_list)
        for interval in interval_list:
            for i in range(interval.begin, interval.end):
                lexatom_seq = TransformFunc(i)

                # Apply sequence to state machine
                state = SM.apply_sequence(lexatom_seq)
                if state is None:
                    error(self.sm, SM, lexatom_seq)

                # All acceptance flags must belong to the original state machine
                acceptance_id_list = [
                    cmd.acceptance_id()
                    for cmd in state.single_entry.get_iterable(SeAccept)
                ]
                if acceptance_id_list and self.id not in acceptance_id_list: 
                    print "\n#UCS:  ", i #, unichr(i)
                    print "#Seq:  ", ["%02X" % x for x in lexatom_seq]
                    print "#acceptance-ids:", acceptance_id_list
                    error(self.sm, SM, lexatom_seq)

        print " (OK=%i)" % interval_count

def error(SM_orig, SM_trafo, LexatomSeq):
    print 
    print "#sm.orig:  ", SM_orig.get_string(NormalizeF=False, Option="hex")
    print "#sm.result:", SM_trafo.get_string(NormalizeF=False, Option="hex")
    # print "#UCS: { interval: %s; value: %s; }" % (interval.get_string(Option="hex"), i)
    print "#Seq: ", ["0x%02X" % x for x in LexatomSeq]
    assert False

def check_negative(SM, ImpossibleIntervals, TransformFunc):
    """None of the given unicode values shall reach an acceptance state.
    """
    print "Inverse Union Check:",
    for interval in ImpossibleIntervals:
        for i in [interval.begin, (interval.end + interval.begin) / 2, interval.end - 1]:
            lexatom_seq = TransformFunc(i)

            # Apply sequence to state machine
            state = SM.apply_sequence(lexatom_seq)
            if state is None: continue

            # An acceptance state cannot be reached by a unicode value in ImpossibleIntervals
            if any(state.single_entry.get_iterable(SeAccept)):
                error(None, SM, lexatom_seq)

    print " (OK)"

def test_on_UCS_sample_sets(Trafo, unicode_to_transformed_sequence):
    script_list = [
        "Arabic", "Armenian", "Balinese", "Bengali", "Bopomofo", "Braille", "Buginese", "Buhid",
        "Canadian_Aboriginal", "Cherokee", "Common",  "Cuneiform",  "Cypriot",  "Deseret",
        "Gothic",  "Greek",  
        "Hanunoo", "Hebrew", "Hiragana", "Inherited", "Kannada", "Han",  
        "Katakana", "Kharoshthi", "Khmer", "Lao", "Latin", "Limbu", "Linear_B", "Malayalam",
        "Mongolian", "Myanmar", "New_Tai_Lue", "Nko", "Osmanya", "Ogham", "Old_Italic", "Old_Persian",
        "Phoenician",  "Shavian",  "Syloti_Nagri", 
        "Syriac", "Tagalog", "Tagbanwa", "Tai_Le", "Tamil", "Telugu", "Thaana", "Thai",
        "Tibetan", "Tifinagh", "Ugaritic", "Yi"
    ]
    sets = [ X(name) for name in script_list ]

    orig = get_combined_state_machine(map(lambda x: x.sm, sets))
    print "# Number of states in state machine:"
    print "#   Unicode:       %i" % len(orig.states)
    verdict_f, result = Trafo.do_state_machine(orig, beautifier)
    print "#   UTF*-Splitted: %i" % len(result.states)

    # print result.get_graphviz_string(Option="hex")

    for set in sets:
        set.check(result, unicode_to_transformed_sequence)
    print "Translated %i groups without abortion on error (OK)" % len(sets)

    union = NumberSet()
    for nset in map(lambda set: set.charset, sets):
        union.unite_with(nset)

    inverse_union = NumberSet(Interval(0, 0x110000))
    inverse_union.subtract(union)
    # print inverse_union.get_string(Option="hex")
    check_negative(result, inverse_union.get_intervals(PromiseToTreatWellF=True), 
                   unicode_to_transformed_sequence)

def show_graphviz(sm):
    gv_str = sm.get_graphviz_string(Option="hex")
    for line in gv_str.splitlines():
        if "->" not in line or "label" not in line: print line; continue
        fields = line.split()
        if len(fields) < 3: 
            print line; continue;
        if len(fields) > 3:
            remainder = reduce(lambda x,y: "%s %s" % (x, y), fields[3:])
        else:
            remainder = ""
        print "((%s)) -> ((%s)) %s" % (fields[0], fields[2], remainder)
