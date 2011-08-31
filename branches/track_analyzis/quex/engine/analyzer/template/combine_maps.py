from quex.engine.generator.state_coder.transition_block import assert_adjacency
from quex.engine.analyzer.template.common               import get_state_list
from quex.engine.interval_handling                      import Interval
from quex.blackboard                                    import E_StateIndices

import sys

def do(StateA, StateB):
    """This function combines two transition maps. A transition map is 
       a list of tuples:

            [
              ...
              (interval, target)
              ...
            ]

       where each tuple tells about a character range [interval.begin, interval.end)
       where the state triggers to the given target. Usually the target is 
       the index of the target state. With template compression, though, multiple
       states are combined. The templates operates on behalf of a state which
       is identified by its 'state_key'. The target may be depend on the state
       key and is thus implemented as an array.

       When two states are combined such information occurs, if the two states
       trigger on the same interval to different targets. Then the entry in the
       transition map must contain where the target triggers dependent on the
       state key, i.e.

            [
              ...
              (interval, target_db)
              ...
            ]

       where the target_db maps:  state_key --> target state

       So, when the templates operates on behalf of a state given by key 'x'
       the target state for a given 'interval' is 'target_db[x]'. Now, this
       mapping may be exactly the same for multiple intervals. Instead of
       storing multiple times the same mapping, an object of class
       TemplateTargetScheme is stored along with the intervals.

       A template state, again, may be combined with other states and other 
       template states. Here, this means that the initial target for an 
       interval in StateA or StateB may already be a TemplateTargetScheme.

       The resulting target map results of the combination of both target
       maps, which may introduce new borders, e.g.
    
                     |----------------|           (where A triggers to X)
                          |---------------|       (where B triggers to Y)

       becomes
                     |----|-----------|---|
                        1       2       3

       where:  Domain:     A triggers to:     B triggers to:
                 1              X               Nothing
                 2              X                  Y
                 3           Nothing               Y

       RETURNS:

               -- resulting transition map.
               -- list of target schemes that have been identified.
    """
    def help(State):
        state_list = get_state_list(State)
        tm         = State.transition_map
        assert_adjacency(tm, TotalRangeF=True)
        return state_list, len(state_list), tm

    StateListA, StateListA_Len, TransitionMapA = help(StateA)
    StateListB, StateListB_Len, TransitionMapB = help(StateB)

    i  = 0 # iterator over interval list 0
    k  = 0 # iterator over interval list 1
    Li = len(TransitionMapA)
    Lk = len(TransitionMapB)

    # Intervals in trigger map are always adjacent, so the '.begin'
    # member is not required.
    scheme_db = TemplateTargetSchemeDB()
    result    = []
    prev_end  = - sys.maxint
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TransitionMapA[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TransitionMapB[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        end       = min(i_end, k_end)
        target    = __get_target(i_target, StateA.index, StateListA_Len,
                                 k_target, StateB.index, StateListB_Len,
                                 scheme_db)

        result.append((Interval(prev_end, end), target))
        prev_end  = end

        if   i_end == k_end: i += 1; k += 1;
        elif i_end <  k_end: i += 1;
        else:                k += 1;

    # Treat the last trigger interval
    target = __get_target(TransitionMapA[-1][1], StateA.index, StateListA_Len,
                          TransitionMapB[-1][1], StateB.index, StateListB_Len,
                          scheme_db)

    result.append((Interval(prev_end, sys.maxint), target))

    return result, scheme_db.get_scheme_list()

class TemplateTargetScheme(object):
    """A target scheme contains the information about what the target
       state is inside an interval for a given template key. For example,
       a given interval X triggers to target scheme T, i.e. there is an
       element in the transition map:

                ...
                [ X, T ]
                ...

       then the tuple 'T.scheme[key]' tells the target state index for
       the case the template operates with the given 'key'. A key in turn,
       stands for a particular state.

       There might be multiple intervals following the same target scheme,
       so the function 'identify_target_schemes()' takes care of making 
       those schemes unique.

       .index  = unique index of the target scheme
                 (unique for the current combination)
       .scheme = target state index scheme as explained above.
    """
    __slots__ = ('index', 'scheme')

    def __init__(self, SchemeIndex, TargetScheme):
        self.index  = SchemeIndex
        self.scheme = TargetScheme

    def __repr__(self):
        return repr(self.scheme)

class TemplateTargetSchemeDB(dict):
    def __init__(self):
        dict.__init__(self)
        
    def get(self, Combination):
        """Checks whether the combination is already present. If so, the reference
           to the existing target scheme is returned. If not a new scheme is created
           and entered into the database.
        """
        result = dict.get(self, Combination)
        if result is None: 
            result            = TemplateTargetScheme(len(self), Combination)
            self[Combination] = result
        return result

    def get_scheme_list(self):
        return self.values()

def __get_target(TA, StateAIndex, StateListA_Len, TB, StateBIndex, StateListB_Len, scheme_db):
    """Generate a target entry for a transition map of combined 
       transition maps for StateA and StateB. 

       TA, TB = Targets of StateA and StateB for one particular 
                character interval.

       RETURNS: An object that tells for what states trigger
                here to what target state. That is:

                -- E_StateIndices.RECURSIVE

                   All related states trigger here to itself.
                   Thus, the template combination triggers to itself.

                -- A scalar integer 'T'

                   All related states trigger to the same target state
                   whose state index is given by the integer T.

                -- A list of integers 'TL'

                   States trigger to different targets. The target state
                   of an involved state with index 'X' is 

                                          TL[i]

                   provided that 
                   
                            (StateListA + StateListB)[i] == X

                   The 'schemes' may be the same for multiple intervals.
                   Thus, they are store in TemplateTargetScheme objects.
                   This is accomplished by function
                   'identify_target_schemes()'.
                
    """
    recursion_n = 0
    # IS RECURSIVE ?
    # -- In a 'normal trigger map' the target needs to be equal to the
    #   state that it contains.
    # -- In a trigger map combination, the recursive target is 
    #    identifier by the value 'E_StateIndices.SAME_STATE'.
    if TA == StateAIndex: TA = E_StateIndices.RECURSIVE
    if TB == StateBIndex: TB = E_StateIndices.RECURSIVE

    # If both transitions are recursive, then the template will
    # contain only a 'recursion flag'. 
    if TA == E_StateIndices.RECURSIVE and TB == E_StateIndices.RECURSIVE:
        return E_StateIndices.RECURSIVE

    # Here: At least one of the targets is not recursive, so we need to expand
    #       any RECURSIVE target to a list of target state indices.
    if TA == E_StateIndices.RECURSIVE: TA = StateAIndex
    if TB == E_StateIndices.RECURSIVE: TB = StateBIndex

    # T = list   -> combination is a 'involved state list'.
    # T = scalar -> same target state for TargetCombinationN in all cases.
    if type(TA) == tuple:
        if type(TB) == tuple: return scheme_db.get(TA                     +  TB                   )
        else:                 return scheme_db.get(TA                     + (TB,) * StateListB_Len)
    else:
        if type(TB) == tuple: return scheme_db.get((TA,) * StateListA_Len +  TB                   )
        elif TA != TB:        return scheme_db.get((TA,) * StateListA_Len + (TB,) * StateListB_Len)
        else:                 return TA # Same Target => Scalar Value


