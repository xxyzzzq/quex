import quex.engine.generator.state.transition_map.solution     as     solution
import quex.engine.generator.state.transition_map.bisection    as     bisection
import quex.engine.generator.state.transition_map.branch_table as     branch_table
import quex.engine.generator.state.transition_map.transition   as     transition
import quex.engine.generator.state.transition_map.comparison_sequence as comparison_sequence
from   quex.blackboard                                  import setup as Setup, Lng
from   copy      import copy
from   itertools import islice

def do(txt, TM):
    assert TM is not None
    assert len(TM) != 0

    # The range of possible characters may be restricted. It must be ensured,
    # that the occurring characters only belong to the admissible range.
    TM.prune(0, Setup.get_buffer_element_value_limit())

    if len(TM) == 1:
        # If there is only one entry,
        # then it MUST cover the the whole range (or more).
        entry = TM[0]
        assert entry[0].begin == 0, "%s" % entry[0]
        assert entry[0].end   == Setup.get_buffer_element_value_limit(), "%s<->%s" % (entry[0].end, Setup.get_buffer_element_value_limit())
        transition.do(txt, entry)
        return

    # (*) Determine 'outstanding' characters. For example, if 'e' appears
    #     exceptionally often, then it makes sense to check:
    #
    #     if( input == 'e' ) {
    #         ...
    #     } else {
    #         /* Rest of transition map. */
    #     }
    #     (Currently, this is a 'no-operation'. It is planned to consider
    #      statitistics about character occurencies into the generation of
    #      the transition map.)
    outstanding_list = solution.prune_outstanding(TM) 
    if outstanding_list is not None: 
        __get_outstanding(txt, outstanding_list)

    # (*) Bisection until other solution is more suitable.
    #     (This may include 'no bisectioning')
    __bisection(txt, TM)

    # (*) When there was an outstanding character, then the whole bisection was
    #     implemented in an 'ELSE' block which must be closed.
    if outstanding_list is not None: 
        txt.append(Lng.ENDIF)

    txt.append("\n%s\n" % Lng.UNREACHABLE)

class SubTriggerMap(object):
    """A trigger map that 'points' into a subset of a trigger map.
       Instead of creating whole new subsets, relate to the original
       trigger map and store 'begin' and 'end' of the new map.
    """
    __slots__ = ("__trigger_map", "__begin_i", "__end_i")

    def __init__(self, TriggerMap):
        self.__trigger_map = TriggerMap
        self.__begin_i     = 0
        self.__end_i       = len(TriggerMap) - 1

    def __getitem__(self, X):
        if isinstance(X, slice):
            result = SubTriggerMap(self.__trigger_map)
            result.__begin_i = self.__begin_i + X.start
            result.__end_i   = self.__begin_i + X.stop
        else:
            return self.__trigger_map[self.__begin_i + X]

    def __len__(self):
        return self.__end_i - self.__begin_i

    def __iter__(self):
        for x in islice(self.__trigger_map, self.__begin_i, self.__end_i):
            yield x

    @property
    def middle(self):
        middle_i = int((self.__end_i - self.__begin_i) / 2) + self.__begin_i
        return self.__trigger_map[middle_i].begin

def debug(TM, Function):
    print "##--BEGIN %s" % Function
    for entry in TM:
        print "##", entry[0]
    print "##--END %s" % Function

def __bisection(txt, TriggerMap):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    global Lng

    T   = len(txt)
    tip = solution.get(TriggerMap)

    # Potentially Recursive
    if   tip == solution.E_Type.BISECTION:           __get_bisection(txt, TriggerMap)
    # Direct Implementation / No more call to __bisection()
    elif tip == solution.E_Type.SWITCH_CASE:         branch_table.do(txt, TriggerMap)
    elif tip == solution.E_Type.COMPARISON_SEQUENCE: comparison_sequence.do(txt, TriggerMap)
    elif tip == solution.E_Type.TRANSITION:          transition.do(txt, TriggerMap[0], IndentF=True)
    else:                                                                 
        assert False

    # (*) Indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    Lng.INDENT(txt, Start=T)

def __get_outstanding(txt, TriggerMapEntry):
    txt.append(Lng.IF_INPUT("==", TriggerMapEntry[0].begin))
    transition.do(txt, TriggerMapEntry)
    txt.append(Lng.ELSE)
    # Caller must provide later for 'ENDIF'

def __get_bisection(txt, TriggerMap):
    
    BisectionIndex = bisection.get_index(TriggerMap)

    lower  = TriggerMap[:BisectionIndex]
    higher = TriggerMap[BisectionIndex:]

    assert len(lower) != 0
    assert len(higher) != 0

    HighBegin = higher[0][0].begin
    LowBegin  = lower[0][0].begin

    def is_single_character(X):
        """RETURNS: True, if interval of X transits on a single character."""
        return len(X) == 1 and X[0][0].size() == 1

    def get_if_statement(InverseF=False):
        if not InverseF:
            # If the size of one interval is 1, then replace the '<' by an '=='.
            if   is_single_character(lower):  return Lng.IF_INPUT("==", LowBegin)
            elif is_single_character(higher): return Lng.IF_INPUT("!=", HighBegin)
            else:                             return Lng.IF_INPUT("<",  HighBegin)
        else:
            # If the size of one interval is 1, then replace the '>=' by an '=='.
            if   is_single_character(lower):  return Lng.IF_INPUT("!=", LowBegin)
            elif is_single_character(higher): return Lng.IF_INPUT("==", HighBegin)
            else:                             return Lng.IF_INPUT(">=", HighBegin)

    # Note, that an '<' does involve a subtraction. A '==' only a comparison.
    # The latter is safe to be faster (or at least equally fast) on any machine.
    txt.append(0)
    txt.append(get_if_statement())
    __bisection(txt, lower)
    txt.append(0)
    txt.append(Lng.ELSE)
    __bisection(txt, higher)

    txt.append(0)
    txt.append(Lng.END_IF())
    txt.append("\n")

def prune_outstanding(TriggerMap):
    """Implements the remaining transitions as:

       (1) Check for an exceptionally often character
       (2) Check for the remaining trigger map
    """
    # Currently no outstanding characters are determined (no statistics yet)
    return None

    #assert TriggerMap[EntryIndex].size() == 1
    #OutstandingCharacter = TriggerMap[EntryIndex].begin

    #if EntryIndex != 0 and EntryIndex != len(TriggerMap) - 1:
    #    # Leave the entry before at size '1' because its easier to test
    #    if   TriggerMap[EntryIndex-1].size() == 1: TriggerMap[EntryIndex+1].begin = OutstandingCharacter
    #    else:                                      TriggerMap[EntryIndex-1].end   = OutstandingCharacter + 1
    #elif EntryIndex == 0:
    #    TriggerMap[EntryIndex+1].begin = OutstandingCharacter
    #elif EntryIndex == len(TriggerMap) - 1:
    #    TriggerMap[EntryIndex-1].begin = OutstandingCharacter

