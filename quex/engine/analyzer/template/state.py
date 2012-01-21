import quex.engine.state_machine.index              as     index
from   quex.engine.generator.state.transition.core  import assert_adjacency
from   quex.engine.analyzer.state_entry             import Entry
from   quex.engine.analyzer.state_entry_action      import SetStateKey, TransitionID
from   quex.engine.interval_handling                import Interval
from   quex.engine.analyzer.core                    import AnalyzerState, get_input_action
from   quex.blackboard                              import E_StateIndices

from itertools   import chain, imap
from collections import defaultdict
import sys

class TemplateState(AnalyzerState):
    """A TemplateState is a state that is implemented to represent multiple
       states.  Tt implements the general scheme and keeps track of the
       particularities. The TemplateState is constructed by 

       The template states are combined successively by the combination of 
       two states where each one of them may also be a TemplateState. The
       combination happes by means of the functions:
       
          combine_maps(...) which combines the transition maps of the 
                            two states into a single transition map that
                            may contain TargetScheme-s. 
                               
          combine_scheme(...) which combines DropOut and Entry schemes
                              of the two states.

       Notably, the derived class TemplateStateCandidate takes an important
       role in the construction of the TemplateState.
    """
    def __init__(self, StateA, StateB):
        # The 'index' remains None, as long as the TemplateState is not an 
        # accepted element of a state machine. This makes sense, in particular
        # for TemplateStateCandidates (derived from TemplateState). 
        self.__index = index.get()

        self.__state_index_list            = get_state_list(StateA) + get_state_list(StateB)
        self.__state_index_to_state_key_db = dict((state_index, i) for i, state_index in enumerate(self.__state_index_list))

        # Combined DropOut and Entry schemes are generated by the same function
        self.__entry = Entry(self.__index, [])
        self.__update_entry(StateA)
        self.__update_entry(StateB)
        self.__entry.finish({})

        self.__drop_out = combine_scheme(get_state_list(StateA), StateA.drop_out, 
                                         get_state_list(StateB), StateB.drop_out)
        self.__uniform_drop_outs_f = (len(self.__drop_out) == 1)
        # If the target of the transition map is a list for a given interval X, i.e.
        #
        #                           (X, target[i]) 
        # 
        # then this means that 
        #
        #      target[i] = target of state 'state_index_list[i]' for interval X.
        #
        self.__transition_map, \
        self.__target_scheme_list = combine_maps(StateA, StateB)

        # Compatible with AnalyzerState
        # (A template state can never mimik an init state)
        self.__engine_type = StateA.engine_type
        self.input = get_input_action(StateA.engine_type, InitStateF=False)

    @property
    def engine_type(self): return self.__engine_type

    @property
    def init_state_f(self):        return False
    @property
    def transition_map(self):      return self.__transition_map
    @property
    def target_scheme_list(self):  return self.__target_scheme_list
    @property
    def state_index_list(self):    return self.__state_index_list
    @property
    def entry(self):               return self.__entry
    @property
    def uniform_drop_outs_f(self): return self.__uniform_drop_outs_f
    @property
    def drop_out(self):            return self.__drop_out

    def state_set_iterable(self, StateIndexList, TheAnalyzer):
        return imap(lambda i: 
                    (i,                                # state_index
                     self.state_index_list.index(i),   # 'state_key' of state (in array)
                     TheAnalyzer.state_db[i]),         # state object
                    StateIndexList)

    def __update_entry(self, TheState):

        print "##SC:", TheState.__class__.__name__
        print "##keys:", TheState.entry.action_db.keys()
        self.__entry.action_db.update(TheState.entry.action_db)

        if isinstance(TheState, TemplateState):
            for transition_id, transition_action in TheState.entry.action_db.iteritems():
                for command in transition_action.command_list.misc:
                    if not isinstance(command, SetStateKey): break
                    new_state_key = self.__state_index_to_state_key_db[transition_id.state_index]
                    command.set_value(new_state_key)
                    break        # There can be only ONE command 'SetStateKey' in a transition_action.
                else:
                    assert False # There MUST be a 'SetStateKey' action in a TemplateState

        elif isinstance(TheState, AnalyzerState):
            for transition_id, transition_action in TheState.entry.action_db.iteritems():
                transition_action.command_list.misc.add(SetStateKey(self.__state_index_to_state_key_db[TheState.index]))
                self.__entry.action_db[transition_id] = transition_action

        else:
            assert False

def combine_scheme(StateIndexListA, A, StateIndexListB, B):
    """A 'scheme' is a dictionary that maps:
             
         (1)       map: object --> state_index_list 

       where for each state referred in state_index_list it holds

         (2)            state.object == object

       For example, if four states 1, 4, 7, and 9 have the same drop_out 
       behavior DropOut_X, then this is stated by an entry in the dictionary as

         (3)       { ...     DropOut_X: [1, 4, 7, 9],      ... }

       For this to work, the objects must support a proper interaction 
       with the 'dict'-objects. Namely, they must support:

         (4)    __hash__          --> get the right 'bucket'.
                __eq__ or __cmp__ --> compare elements of 'bucket'.

       The dictionaries are implemented as 'defaultdict(list)' so that 
       the state index list can simply be 'extended' from scratch.

       NOTE: This type of 'scheme', as mentioned in (1) and (2) is suited 
             for DropOut and EntryObjects. It is fundamentally different 
             from a TargetScheme T of transition maps, where T[state_key] 
             maps to the target state of state_index_list[state_key].
    """
    # A and B can be 'objects' or dictionaries that map 'object: -> state_index_list'
    # where the 'state_index_list' is the set of states that have the 'object'.
    A_iterable = get_iterable(A, StateIndexListA)
    B_iterable = get_iterable(B, StateIndexListB)
    # '*_iterable' represent lists of pairs '(object, state_index_list)' 

    result = defaultdict(list)
    for element, state_index_list in chain(A_iterable, B_iterable):
        assert hasattr(element, "__hash__")
        assert hasattr(element, "__eq__")
        result[element].extend(state_index_list)

    return result

def combine_maps(StateA, StateB):
    """RETURNS:

          -- Transition map = combined transition map of StateA and StateB.

          -- List of target schemes that have been identified.

       NOTE: 

       If the entries of both states are uniform, then a transition to itself
       of both states can be implemented as a recursion of the template state
       without knowing the particular states.

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
       Thus, TargetSchemes must be combined with trigger targets
       and other TargetSchemes.

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

    -----------------------------------------------------------------------------
    Transition maps of TemplateState-s function based on 'state_keys'. Those state
    keys are used as indices into TemplateTargetSchemes. The 'state_key' of a given
    state relates to the 'state_index' by

        (1)    self.state_index_list[state_key] == state_index

    where 'state_index' is the number by which the state is identified inside
    its state machine. Correspondingly, for a given TemplateTargetScheme T 

        (2)                   T[state_key]

    gives the target of the template if it operates for 'state_index' determined
    from 'state_key' by relation (1). The state index list approach facilitates the
    computation of target schemes. For this reason no dictionary
    {state_index->target} is used.
    """
    def __help(State):
        tm         = State.transition_map
        assert_adjacency(tm, TotalRangeF=True)
        return tm, len(tm)

    TransitionMapA, LenA = __help(StateA)
    TransitionMapB, LenB = __help(StateB)

    i  = 0 # iterator over TransitionMapA
    k  = 0 # iterator over TransitionMapB

    # Intervals in trigger map are always adjacent, so the '.begin' member is
    # not required.
    scheme_db = TargetSchemeDB(StateA, StateB)
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
        target    = scheme_db.get_target(i_target, k_target)

        result.append((Interval(prev_end, end), target))
        prev_end  = end

        if   i_end == k_end: i += 1; k += 1;
        elif i_end <  k_end: i += 1;
        else:                k += 1;

    # Treat the last trigger interval
    target = scheme_db.get_target(TransitionMapA[-1][1], TransitionMapB[-1][1])

    result.append((Interval(prev_end, sys.maxint), target))

    return result, scheme_db.get_scheme_list()

class TargetScheme(object):
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
       so the function 'TargetSchemeDB.get()' takes care of making 
       those schemes unique.

           .scheme = Target state index scheme as explained above.

           .index  = Unique index of the target scheme. This value is 
                     determined by 'TargetSchemeDB.get()'. It helps
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

    def __hash__(self):
        return self.__index

    def __eq__(self, Other):
        if isinstance(Other, TargetScheme) == False: return False
        return self.__scheme == Other.__scheme

class TargetSchemeDB(dict):
    """A TargetSchemeDB keeps track of existing target state combinations.
       If a scheme appears more than once, it does not get a new index. By means
       of the index it is possible to avoid multiple definitions of the same 
       scheme, later.
    """
    def __init__(self, StateA, StateB):
        dict.__init__(self)
        self.__state_a_index                   = StateA.index
        self.__state_a_state_index_list        = get_state_list(StateA)
        self.__state_a_state_index_list_length = len(self.__state_a_state_index_list)
        self.__state_b_index                   = StateB.index
        self.__state_b_state_index_list        = get_state_list(StateB)
        self.__state_b_state_index_list_length = len(self.__state_b_state_index_list)
        
    def get(self, Targets):
        """Checks whether the combination is already present. If so, the reference
           to the existing target scheme is returned. If not a new scheme is created
           and entered into the database.

           The TargetScheme must be a tuple, such as 

              (1, E_StateIndices.DROP_OUT, 4, ...)

           which tells that if the template operates with

              -- state_key = 0 (first element) there must be a transition to state 1, 
              -- state_key = 1 (second element), then there must be a drop-out,
              -- state_key = 2 (third element), then transit to state 4,
              -- ...
        """
        assert isinstance(Targets, tuple)
        for target in Targets:
            assert isinstance(target, (int, long)) or target == E_StateIndices.DROP_OUT

        result = dict.get(self, Targets)
        if result is None: 
            new_index     = len(self)
            result        = TargetScheme(new_index, Targets)
            self[Targets] = result
        return result

    def get_scheme_list(self):
        return self.values()

    def get_target(self, TA, TB):
        """Generate a target entry for a transition map of combined transition maps
           of StateA and StateB. 

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
               are store in TargetScheme objects.  This is accomplished by
               function 'TargetSchemeDB.get()'.
        """
        assert isinstance(TA, (long, TargetScheme)) or TA in E_StateIndices, "%s" % TA.__class__.__name__
        assert isinstance(TB, (long, TargetScheme)) or TB in E_StateIndices, "%s" % TB.__class__.__name__

        StateAIndex = self.__state_a_index
        StateListA  = self.__state_a_state_index_list
        StateBIndex = self.__state_b_index
        StateListB  = self.__state_b_state_index_list

        # IS RECURSIVE ?
        # -- In a 'normal trigger map' the target needs to be equal to the
        #    state that it contains.
        # -- In a trigger map combination, the recursive target is 
        #    identifier by the value 'E_StateIndices.SAME_STATE'.
        # (If a "StateIndex is None" then it must be a TemplateStateCandidate.
        #  Those cannot be recursive, except explicitly by a target = E_StateIndices.RECURSIVE)
        if StateAIndex is not None and TA == StateAIndex: TA = E_StateIndices.RECURSIVE
        if StateBIndex is not None and TB == StateBIndex: TB = E_StateIndices.RECURSIVE

        # If both transitions are recursive, then the template will
        # contain only a 'recursion flag'. 
        if TA == E_StateIndices.RECURSIVE and TB == E_StateIndices.RECURSIVE:
            return E_StateIndices.RECURSIVE

        # Here: At least one of the targets is not recursive, so we need to expand
        #       any RECURSIVE target to a list of target state indices. For recursive
        #       states, the target states are the states itself in the order they
        #       are listed in 'state_index_list'.
        def adapt(T, StateList):
            if T == E_StateIndices.RECURSIVE: 
                if len(StateList) == 1:       return StateList[0]
                else:                         return tuple(StateList)
            elif isinstance(T, TargetScheme): return T.scheme
            else:                             return T

        TA = adapt(TA, StateListA)
        TB = adapt(TB, StateListB)

        # T = tuple  -> combination is a 'involved state list'.
        # T = scalar -> same target state for TargetCombinationN in all cases.
        StateListA_Len = self.__state_a_state_index_list_length
        StateListB_Len = self.__state_b_state_index_list_length

        if isinstance(TA, tuple):
            if isinstance(TB, tuple): return self.get(TA              +  TB                   )
            else:                     return self.get(TA              + (TB,) * StateListB_Len)
        else:
            if isinstance(TB, tuple): return self.get((TA,) * StateListA_Len +  TB                   )
            elif TA != TB:            return self.get((TA,) * StateListA_Len + (TB,) * StateListB_Len)
            else:                     return TA # Same Target => Scalar Value

def get_state_list(X): 
    if isinstance(X, TemplateState): return X.state_index_list 
    else:                            return [ X.index ]

def get_iterable(X, StateIndexList): 
    if isinstance(X, defaultdict): return X.iteritems()
    else:                          return [(X, StateIndexList)]

