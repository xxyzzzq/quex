from quex.blackboard import TargetStateIndices

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

def do(StateListA, TransitionMapA, StateListB, TransitionMapB):
    StateListA_Len = len(StateListA)
    StateListB_Len = len(StateListB)

    def __asserts(TM):
        """-- first border at - sys.maxint
           -- all intervals are adjacent (current begin == previous end)
           -- last border at  + sys.maxint
        """
        prev_end = -sys.maxint
        for x in TM:
            assert x[0].begin == prev_end
            prev_end = x[0].end
        assert TM[-1][0].end  == sys.maxint

    def __get_target(TA, TB):
        """Generate a target entry for a transition map of combined 
           transition maps for StateA and StateB. 

           TA, TB = Targets of StateA and StateB for one particular 
                    character interval.

           RETURNS: An object that tells for what states trigger
                    here to what target state. That is:

                    -- TargetStateIndices.RECURSIVE

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
        #    identifier by the value 'TargetStateIndices.SAME_STATE'.
        if TA == StateA.index: TA = TargetStateIndices.RECURSIVE
        if TB == StateB.index: TB = TargetStateIndices.RECURSIVE

        # If both transitions are recursive, then the template will
        # contain only a 'recursion flag'. 
        if TA == TargetStateIndices.RECURSIVE and TB == TargetStateIndices.RECURSIVE:
            return TargetStateIndices.RECURSIVE

        # Here: At least one of the targets is not recursive, so we need to expand
        #       any RECURSIVE target to a list of target state indices.
        if TA == TargetStateIndices.RECURSIVE: TA = StateListA
        if TB == TargetStateIndices.RECURSIVE: TB = StateListA

        # T = list   -> combination is a 'involved state list'.
        # T = scalar -> same target state for TargetCombinationN in all cases.
        if type(TA) == tuple:
            if type(TB) == tuple: return  TA                   +  TB
            else:                 return  TA                   + (TB,) * StateListB_Len
        else:
            if type(TB) == tuple: return (TA,) * StateListA_Len +  TB
            elif TA != TB:        return (TA,) * StateListA_Len + (TB,) * StateListB_Len
            else:                 return TA                      # Same Target => Scalar Value

    __asserts(TransitionMapA)
    __asserts(TransitionMapB)

    i  = 0 # iterator over interval list 0
    k  = 0 # iterator over interval list 1
    Li = len(TransitionMapA)
    Lk = len(TransitionMapB)

    # Intervals in trigger map are always adjacent, so the '.begin'
    # member is not required.
    result   = []
    prev_end = - sys.maxint
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TransitionMapA[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TransitionMapB[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        end       = min(i_end, k_end)
        target    = __get_target(i_target, k_target)
        result.append(prev_end, end, target)
        prev_end  = end

        if   i_end == k_end: i += 1; k += 1;
        elif i_end <  k_end: i += 1;
        else:                k += 1;

    # Treat the last trigger interval
    target = __get_target(TransitionMapA[-1][1], TransitionMapB[-1][1])
    result.append(prev_end, sys.maxint, target)

    target_scheme_db = adapt_target_schemes(result)

    return result, target_scheme_db

def adapt_target_schemes(result):
    """Identify target schemes, i.e. intervals where all involved states
       trigger to similar targets.

       MODIFIES: result

                 Lines where states differ in the target state (tuples)
                 are replaced with objects of class TemplateTargetScheme.

       RETURNS:  target scheme database, i.e. a map

                 combination --> TemplateTargetScheme that represents
                                 the combination.
    """
    i = -1
    for element in ifilter(lambda x: isinstance(x, tuple), result):
        target = element[1]
        scheme = db.get(target)
        if scheme is not None: 
            element[1] = scheme
        else: 
            i += 1
            new_entry  = TemplateTargetScheme(i, target)
            db[target] = new_entry
            element[1] = new_entry
    return db


