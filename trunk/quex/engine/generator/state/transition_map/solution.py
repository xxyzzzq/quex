import quex.engine.generator.state.transition_map.bisection           as bisection
import quex.engine.generator.state.transition_map.branch_table        as branch_table
import quex.engine.generator.state.transition_map.transition          as transition
import quex.engine.generator.state.transition_map.comparison_sequence as comparison_sequence

from   quex.engine.misc.enum import Enum
from   math                  import log

def do(TM):
    return get_structure(TM)

def get_structure(TM): 
    """__dive --> indicate recursion that might be replaced by TreeWalker
    """
    interval_n = len(TM)
    assert interval_n > 1

    moat = TM.get_most_often_appearing_target()

    # If there's only one interval, there's no need to compare, just go!
    # Otherwise, if there's a very low number of intervals, make a small
    # comparison list that iterates linearly through the items.
    if interval_n < 4:  return ComparisonSequence(TM, moat)

    # If the size of character ranges which do not target 'moat' is less
    # than a certain number, implement the transition as branch table. The
    # 'moat' is implemented as the 'default:' case.
    sz_non_moat = TM.get_size_of_range_other_targets(moat)
    if sz_non_moat > 256: return BranchTable(TM, moat)

    # Else, there is nothing left but bisectioning
    # (which is not the worst thing to do)
    tm0, tm1 = get_bisection(TM)
    bisection_value = tm0[-1][0].end
    low  = get_structure(tm0)
    high = get_structure(tm1)
    return Bisection(bisection_value, low, high)

def get_bisection(TM):
    """Currently: very simplest solution 'the middle'
    """
    L = len(TM)
    assert L > 1
    index = int(L / 2)
    return TM[:index], TM[index:]

