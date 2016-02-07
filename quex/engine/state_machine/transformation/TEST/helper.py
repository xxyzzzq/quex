import quex.input.regular_expression.engine                       as     regex
from   quex.engine.state_machine.state.single_entry               import SeAccept     
from   quex.engine.state_machine.core                             import StateMachine
from StringIO import StringIO

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
        print "Name = " + self.name, 
        for interval in self.charset.get_intervals(PromiseToTreatWellF=True):
            for i in range(interval.begin, interval.end):
                utf16_seq = TransformFunc(i)

                # Apply sequence to state machine
                state = SM.apply_sequence(utf16_seq)
                assert state is not None, \
                       "No acceptance for %X in [%X,%X] --> %s" % \
                       (i, interval.begin, interval.end - 1, repr(map(lambda x: "%04X." % x, utf16_seq)))

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

        print " (OK=%i)" % self.id

def check_negative(SM, ImpossibleIntervals, TransformFunc):
    """None of the given unicode values shall reach an acceptance state.
    """
    print "Inverse Union Check:",
    for interval in ImpossibleIntervals:
        for i in [interval.begin, (interval.end + interval.begin) / 2, interval.end - 1]:
            utf16_seq = TransformFunc(i)

            # Apply sequence to state machine
            state = SM.apply_sequence(utf16_seq)
            if state is None: continue

            # An acceptance state cannot be reached by a unicode value in ImpossibleIntervals
            assert not any(state.single_entry.get_iterable(SeAccept))

    print " (OK)"
