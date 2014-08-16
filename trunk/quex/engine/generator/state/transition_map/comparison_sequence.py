import quex.engine.generator.state.transition_map.transition as     transition
from quex.blackboard import setup as Setup, \
                            Lng

def do(txt, TriggerMap):
    global Lng

    L = len(TriggerMap)
    trigger_map = TriggerMap

    # Depending on whether the list is checked forward or backward,
    # the comparison operator and considered border may change.
    _border_cmp = "<"
    _border     = lambda interval: interval.end

    # The buffer limit code is something extreme seldom, so make sure that it is 
    # tested at last, if it is there. This might require to reverse the trigger map.
    if     Setup.buffer_limit_code >= TriggerMap[0][0].begin \
       and Setup.buffer_limit_code < TriggerMap[-1][0].end:
        # Find the index of the buffer limit code in the list
        for i, candidate in enumerate(TriggerMap):
            if candidate[0].contains(Setup.buffer_limit_code): break
        if i < L / 2:
            trigger_map = copy(TriggerMap)
            trigger_map.reverse()
            _border_cmp = ">="
            _border     = lambda interval: interval.begin

    assert len(trigger_map) != 0
    L = len(trigger_map)

    LastI = L - 1
    code = []
    for i, entry in enumerate(trigger_map):
        interval, target = entry

        if i != 0: code.append("\n")
        if   i == LastI:           code.append(Lng.ELSE)
        elif interval.size() == 1: code.append(Lng.IF_INPUT("==", interval.begin, i==0))
        else:                      code.append(Lng.IF_INPUT(_border_cmp, _border(interval), i==0))

        transition.do(code, entry, IndentF=True)

    code.append("\n%s\n" % Lng.END_IF(LastF=True))

    txt.extend(code)
    return True

