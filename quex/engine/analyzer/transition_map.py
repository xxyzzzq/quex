from   quex.engine.interval_handling import Interval
from   quex.blackboard import E_StateIndices
import sys
from bisect import bisect_left, bisect_right

def zipped_iterable(TransitionMapA, TransitionMapB):
    """Produces an iterable over two transition maps at once. The borders in the
    zipped transition map consist of a superset of all borders of transition
    map 'A' and 'B'. Whenever a border hits a new interval is notified. 

            YIELDS:  begin, end, a_target, b_target

    Interval [begin, end) is homogenous in the zipped transition map, i.e.
    inside this interval 'A' triggers to 'a_target' and 'B' to 'b_target'.  
    """
    LenA             = len(TransitionMapA)
    LenB             = len(TransitionMapB)
    i                = 0 # iterator over TransitionMapA
    k                = 0 # iterator over TransitionMapB
    i_itvl, i_target = TransitionMapA[i]
    k_itvl, k_target = TransitionMapB[k]
    prev_end         = - sys.maxint
    # Intervals in trigger map are always adjacent, so the '.begin' member is
    # not accessed.
    while not (i == LenA - 1 and k == LenB - 1):
        end    = min(i_itvl.end, k_itvl.end)

        yield prev_end, end, i_target, k_target

        prev_end  = end

        if   i_itvl.end == k_itvl.end: 
            i += 1; i_itvl, i_target = TransitionMapA[i]
            k += 1; k_itvl, k_target = TransitionMapB[k]
        elif i_itvl.end <  k_itvl.end: 
            i += 1; i_itvl, i_target = TransitionMapA[i]
        else:                          
            k += 1; k_itvl, k_target = TransitionMapB[k]

    # Treat the last trigger interval
    yield prev_end, sys.maxint, TransitionMapA[-1][1], TransitionMapB[-1][1]
    return

def relate_to_door_ids(transition_map, TheAnalyzer, StateIndex):
    """Creates a transition_map that triggers to DoorIDs instead of target states.
    """
    def adapt(Target):
        if Target == E_StateIndices.DROP_OUT:
            return Target
        else:
            return TheAnalyzer.state_db[Target].entry.get_door_id(StateIndex=Target, FromStateIndex=StateIndex),

    return [(interval, adapt(target)) for interval, target in transition_map]

def bisect_begin(transition_map, Value, lower=0):
    """Find entry 'i' by bisectioning so that it holds:

          -- transition_map[i][0].begin <= Value
          -- transition_map[k][0].begin > Value for all k > i
    """
    upper = len(transition_map)
    delta = upper - lower
    while delta > 1:
        i       = lower + delta / 2
        current = transtion_map[i][0].begin
        if   current > Value: upper = i 
        elif current < Value: lower = i
        else:                 return i
        delta   = upper - lower

    return lower if transition_map[lower][0].begin == Value else -1

def set(transition_map, Character, NewTarget):
    # (bisectioning would certainly be more elegant ...)
    for i, entry in enumerate(transition_map):
        interval, target = entry
        if interval.contains(Character):
            break
    else:
        assert False, "Character does not lie inside transition map."

    # Found the interval that contains the Character
    assert interval.size() > 0

    if interval.size() == 1: 
        transition_map[i] = (interval, NewTarget)

    elif Character == interval.begin:
        transition_map.insert(i, (Interval(Character), NewTarget))
        transition_map[i+1][0].begin = Character + 1

    elif Character == interval.end - 1:
        transition_map[i][0].end = Character 
        transition_map.insert(i+1, (Interval(Character), NewTarget))

    else:
        transition_map.insert(i+1, (Interval(Character), NewTarget))
        transition_map.insert(i+2, (Interval(Character+1, interval.end), target))
        transition_map[i][0].end = Character 

    return

