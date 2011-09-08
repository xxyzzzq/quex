from quex.engine.generator.state_coder.transition_block import assert_adjacency
from quex.engine.analyzer.template.common               import get_state_list
from quex.engine.interval_handling                      import Interval
from quex.blackboard                                    import E_StateIndices

import sys

def do(StateA, StateB):
    """RETURNS:

          -- Transition map = combined transition map of StateA and StateB.

          -- List of target schemes that have been identified.

       EXPLANATION:
    
       This function combines two transition maps. A transition map is a list
       of tuples:

            [
              ...
              (interval, target)
              ...
            ]

       Each tuple tells about a character range [interval.begin, interval.end)
       where the state triggers to the given target. In a normal AnalyzerState
       the target is the index of the target state. In a TemplateState, though,
       multiple states are combined. A TemplateState operates on behalf of a
       state which is identified by its 'state_key'. 
       
       If two states (even TemplateStates) are combined the trigger maps
       are observed, e.g.

            Trigger Map A                    Trigger Map B
                                                                          
            [                                [
              ([0,  10),   DropOut)            ([0,  10),   State_4)
              ([10, 15),   State_0)            ([10, 15),   State_1)
              ([15, 20),   DropOut)            ([15, 20),   State_0)
              ([20, 21),   State_1)            ([20, 21),   DropOut)
              ([21, 255),  DropOut)            ([21, 255),  State_0)
            ]                                ]                           


       For some intervals, the target is the same. But for some it is different.
       In a TemplateState, the intervals are associated with TargetScheme 
       objects. A TargetScheme object tells the target state dependent
       on the 'state_key'. The above example may result in a transition map
       as below:

            Trigger Map A                   
                                                                          
            [     # intervals:   target schemes:                           
                  ( [0,  10),    { A: DropOut,   B: State_4, },
                  ( [10, 15),    { A: State_0,   B: State_1, },
                  ( [15, 20),    { A: DropOut,   B: State_0, },
                  ( [20, 21),    { A: State_1,   B: DropOut, },
                  ( [21, 255),   { A: DropOut,   B: State_0, },
            ]                                                           

       Note, that the 'scheme' for interval [12, 20) and [21, 255) are identical.
       We try to profit from it by storing only it only once. A template scheme
       is associated with an 'index' for reference.

       TemplateStates may be combined with AnalyzerStates and other TemplateStates.
       Thus, TemplateTargetSchemes must be combined with trigger targets
       and other TemplateTargetSchemes.

       NOTE:

       The resulting target map results from the combination of both transition
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

    """
    def __help(State):
        state_list = get_state_list(State)
        tm         = State.transition_map
        assert_adjacency(tm, TotalRangeF=True)
        return state_list, len(state_list), tm, len(tm)

    StateListA, StateListA_Len, TransitionMapA, LenA = __help(StateA)
    StateListB, StateListB_Len, TransitionMapB, LenB = __help(StateB)

    i  = 0 # iterator over TransitionMapA
    k  = 0 # iterator over TransitionMapB

    # Intervals in trigger map are always adjacent, so the '.begin' member is
    # not required.
    scheme_db = TemplateTargetSchemeDB()
    result    = []
    prev_end  = - sys.maxint
    while not (i == LenA - 1 and k == LenB - 1):
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

       then 'T.scheme[key]' tells the target state index for the case the
       template operates with the given 'key'. A key in turn, stands for a
       particular state.

       There might be multiple intervals following the same target scheme,
       so the function 'TemplateTargetSchemeDB.get()' takes care of making 
       those schemes unique.

           .scheme = Target state index scheme as explained above.

           .index  = Unique index of the target scheme. This value is 
                     determined by 'TemplateTargetSchemeDB.get()'. It helps
                     later to define the scheme only once, even it appears
                     twice or more.
    """
    __slots__ = ('__index', '__scheme')

    def __init__(self, UniqueIndex, TargetScheme):
        assert isinstance(TargetScheme, tuple)

        self.__scheme = TargetScheme
        self.__index  = UniqueIndex

    @property
    def scheme(self): return self.__scheme

    @property
    def index(self):  return self.__index

    def __repr__(self):
        return repr(self.__scheme)

class TemplateTargetSchemeDB(dict):
    """A TemplateTargetSchemeDB keeps track of existing target state combinations.
       If a scheme appears more than once, it does not get a new index. By means
       of the index it is possible to avoid multiple definitions of the same 
       scheme, later.
    """
    def __init__(self):
        dict.__init__(self)
        
    def get(self, TargetScheme):
        """Checks whether the combination is already present. If so, the reference
           to the existing target scheme is returned. If not a new scheme is created
           and entered into the database.

           The TargetScheme must be a tuple, such as 

              (1, E_StateIndices.DROP_OUT, 4, E_StateIndices.DROP_OUT, 1)

           which tells that if the template operates on behalf of state_key 0
           there must be a transition to state 1, if state_key = 1, then there
           must be a 'drop-out', etc.
        """
        assert isinstance(TargetScheme, tuple)

        result = dict.get(self, TargetScheme)
        if result is None: 
            result             = TemplateTargetScheme(len(self), TargetScheme)
            self[TargetScheme] = result
        return result

    def get_scheme_list(self):
        return self.values()

def __get_target(TA, StateAIndex, StateListA_Len, TB, StateBIndex, StateListB_Len, scheme_db):
    """Generate a target entry for a transition map of combined transition maps
       for StateA and StateB. 

           TA, TB = Targets of StateA and StateB for one particular character
                    interval.

       RETURNS: 
       
       An object that tells for what states trigger here to what target state.
       That is:

        -- E_StateIndices.RECURSIVE

           All related states trigger here to itself.  Thus, the template
           combination triggers to itself.

        -- A scalar integer 'T'

           All related states trigger to the same target state whose state
           index is given by the integer T.

        -- A list of integers 'TL'

           States trigger to different targets. The target state of an involved
           state with index 'X' is 

                                  TL[i]

           provided that 

                    (StateListA + StateListB)[i] == X

           The 'schemes' may be the same for multiple intervals.  Thus, they
           are store in TemplateTargetScheme objects.  This is accomplished by
           function 'TemplateTargetSchemeDB.get()'.
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


