import quex.engine.generator.state.transition_map.transition as transition
from   quex.blackboard import setup as Setup, \
                              Lng

class ComparisonSequence(object):
    __slots__ = ("sub_map", "moat")
    def __init__(self, SubMap, Moat):
        Node.__init__(self, ImplementFunc)
        self.sub_map = SubMap
        self.moat    = Moat

    def implement(self):
        global Lng

        trigger_map = self.sub_map
        L = len(trigger_map)

        # Depending on whether the list is checked forward or backward,
        # the comparison operator and considered border may change.
        _border_cmp = "<"
        _border     = lambda interval: interval.end

        # The buffer limit code is something extreme seldom, so make sure that it is 
        # tested at last, if it is there. This might require to reverse the trigger map.
        blc_index = tm.index(Setup.buffer_limit_code)
        if blc_index is not None and blc_index < L / 2:
            trigger_map = copy(TriggerMap)
            trigger_map.reverse()
            _border_cmp = ">="
            _border     = lambda interval: interval.begin

        assert len(trigger_map) != 0
        L = len(trigger_map)

        LastI = L - 1
        code  = []
        for i, entry in enumerate(trigger_map):
            interval, target = entry

            if i != 0: code.append("\n")
            if   i == LastI:           code.append(Lng.ELSE)
            elif interval.size() == 1: code.append(Lng.IF_INPUT("==", interval.begin, i==0))
            else:                      code.append(Lng.IF_INPUT(_border_cmp, _border(interval), i==0))

            code.extend(transition.do(interval, target))

        code.append("\n%s\n" % Lng.END_IF(LastF=True))

        txt.extend(code)
        return True

