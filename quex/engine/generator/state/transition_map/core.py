import quex.engine.generator.state.transition_map.bisection           as bisection
import quex.engine.generator.state.transition_map.branch_table        as branch_table
import quex.engine.generator.state.transition_map.transition          as transition
import quex.engine.generator.state.transition_map.comparison_sequence as comparison_sequence
import quex.engine.generator.state.transition_map.solution            as     solution
from   quex.blackboard                                                import setup as Setup, Lng
from   copy      import copy
from   itertools import islice

def do(txt, TM):
    # The range of possible characters may be restricted. It must be ensured,
    # that the occurring characters only belong to the admissible range.
    TM.prune(0, Setup.get_buffer_element_value_limit())

    _assert_consistency(TM)

    structure = solution.do(TM)
    # (*) Bisection until other solution is more suitable.
    #     (This may include 'no bisectioning')
    _implement(txt, structure)

    txt.append("\n%s\n" % Lng.UNREACHABLE)

def _implement(txt, structure):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    global Lng

    # Potentially Recursive
    txt.append(E_TextCmd.INDENT)
    txt.extend(structure.implement())
    txt.append(E_TextCmd.DEDENT)

def _assert_consistency(TM):
    assert TM is not None
    assert len(TM) != 0

    if len(TM) != 1: return
    # If there is only one entry,
    # then it MUST cover the the whole range (or more).
    entry = TM[0]
    assert entry[0].begin == 0, "%s" % entry[0]
    assert entry[0].end   == Setup.get_buffer_element_value_limit(), "%s<->%s" % (entry[0].end, Setup.get_buffer_element_value_limit())

