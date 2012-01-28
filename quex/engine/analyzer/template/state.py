import quex.engine.state_machine.index              as     index
from   quex.engine.generator.state.transition.core  import assert_adjacency
from   quex.engine.analyzer.state_entry             import Entry
from   quex.engine.analyzer.state_entry_action      import SetStateKey, TransitionID, DoorID
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
    def __init__(self, StateA, StateB, TheAnalyzer):
        # The 'index' remains None, as long as the TemplateState is not an 
        # accepted element of a state machine. This makes sense, in particular
        # for TemplateStateCandidates (derived from TemplateState). 
        AnalyzerState.set_index(self, index.get())

        self.__state_index_list            = get_state_list(StateA) + get_state_list(StateB)
        self.__state_index_to_state_key_db = dict((state_index, i) for i, state_index in enumerate(self.__state_index_list))

        # Combined DropOut and Entry schemes are generated by the same function
        self.__entry = Entry(self.index, [])
        self.__update_entry(StateA)
        self.__update_entry(StateB)
        self.__entry.finish(None)

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
        self.__target_scheme_list = combine_maps(StateA, StateB, TheAnalyzer)

        # Compatible with AnalyzerState
        # (A template state can never mimik an init state)
        self.__engine_type = StateA.engine_type
        self.input         = get_input_action(StateA.engine_type, InitStateF=False)

    def replace_door_ids_in_transition_map(self, ReplacementDB):
        def replace_if_required(DoorId):
            replacement = ReplacementDB.get(DoorId)
            if replacement is not None: return replacement
            return DoorId

        for interval, target in self.__transition_map:
            if target.drop_out_f or target.recursive_f: continue

            if target.door_id is not None:
                new_door_id = ReplacementDB.get(target.door_id)
                if new_door_id is not None:
                    target.door_id_replace(new_door_id)
            else:
                new_scheme = tuple(replace_if_required(door_id) for door_id in target.scheme)
                target.scheme_replace(new_scheme)

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
    @property
    def entries_empty_f(self):
        """The 'SetStateKey' commands cost nothing, so an easy condition for
           'all entries empty' is that the door_tree_root reports a cost of '0'.
        """
        # This function can only be called after a call to 'finish()'.
        assert self.entry.door_tree_root is not None
        return self.entry.door_tree_root.has_commands_other_than_SetStateKey()

    def __update_entry(self, TheState):

        for transition_id, action in TheState.entry.action_db.iteritems():
            clone       = action.clone()
            state_index = transition_id.state_index
            state_key   = self.__state_index_to_state_key_db[transition_id.state_index]
            for command in clone.command_list.misc:
                if not isinstance(command, SetStateKey): continue
                command.set_value(state_key)
                break
            else:
                clone.command_list.misc.add(SetStateKey(state_key))

            self.__entry.action_db[transition_id] = clone

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

def combine_maps(StateA, StateB, TheAnalyzer):
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
    scheme_db = TargetSchemeDB(StateA, StateB, TheAnalyzer)
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
        assert isinstance(target, TargetScheme)

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

       then 'T.scheme[key]' tells the 'door id' of the door that is entered
       for the case the operates with the given 'key'. A key in turn, stands 
       for a particular state.

       There might be multiple intervals following the same target scheme,
       so the function 'TargetSchemeDB.get()' takes care of making 
       those schemes unique.

           .scheme = Target state index scheme as explained above.

           .index  = Unique index of the target scheme. This value is 
                     determined by 'TargetSchemeDB.get()'. It helps
                     later to define the scheme only once, even it appears
                     twice or more.
    """
    __slots__ = ('__index', '__scheme', '__drop_out_f', '__recursive_f', '__door_id', '__scheme')

    def __init__(self, Target, UniqueIndex=None):
        if UniqueIndex is not None: 
            assert isinstance(Target, tuple)
        else:
            assert    isinstance(Target, DoorID) \
                   or Target == E_StateIndices.DROP_OUT \
                   or Target == E_StateIndices.RECURSIVE

        self.__index       = UniqueIndex

        self.__drop_out_f  = False
        self.__recursive_f = False
        self.__door_id     = None
        self.__scheme      = None

        if   Target == E_StateIndices.DROP_OUT:  self.__drop_out_f  = True;   assert UniqueIndex is None
        elif Target == E_StateIndices.RECURSIVE: self.__recursive_f = True;   assert UniqueIndex is None
        elif isinstance(Target, DoorID):         self.__door_id     = Target; assert UniqueIndex is None
        elif isinstance(Target, tuple):          self.__scheme      = Target; assert UniqueIndex is not None

    @property
    def scheme(self):      return self.__scheme

    def scheme_replace(self, Scheme):
        assert isinstance(Scheme, tuple)
        assert self.__scheme is not None
        self.__scheme = Scheme

    @property
    def door_id(self):     return self.__door_id

    def door_id_replace(self, DoorId):
        assert isinstance(DoorId, DoorID)
        assert self.__door_id is not None
        self.__door_id = DoorId

    @property
    def drop_out_f(self):  return self.__drop_out_f

    @property
    def recursive_f(self): return self.__recursive_f

    @property
    def index(self):       return self.__index

    def __repr__(self):
        if   self.drop_out_f:          return "TargetScheme:DropOut"
        elif self.recursive_f:         return "TargetScheme:Recursion"
        elif self.door_id is not None: return "TargetScheme:(%s)" % repr(self.__door_id)
        elif self.scheme  is not None: return "TargetScheme:(%s)" % repr(self.__scheme)
        else:                          return "TargetScheme:<ERROR>"

    def __hash__(self):
        return self.__index

    def __eq__(self, Other):
        if isinstance(Other, TargetScheme) == False: return False
        ## if self.__index != Other.__index: return False
        return self.__scheme == Other.__scheme

class TargetSchemeDB(dict):
    """A TargetSchemeDB keeps track of existing target state combinations.
       If a scheme appears more than once, it does not get a new index. By means
       of the index it is possible to avoid multiple definitions of the same 
       scheme, later.
    """
    def __init__(self, StateA, StateB, TheAnalyzer):
        dict.__init__(self)
        self.__analyzer                        = TheAnalyzer
        self.__state_a                         = StateA
        self.__state_a_template_state_f        = isinstance(StateA, TemplateState)
        self.__state_a_index                   = StateA.index
        self.__state_a_state_index_list        = get_state_list(StateA)
        self.__state_a_state_index_list_length = len(self.__state_a_state_index_list)
        self.__state_b                         = StateB
        self.__state_b_template_state_f        = isinstance(StateB, TemplateState)
        self.__state_b_index                   = StateB.index
        self.__state_b_state_index_list        = get_state_list(StateB)
        self.__state_b_state_index_list_length = len(self.__state_b_state_index_list)

        # Determine whether the recursion (if it appears) happens without any
        # action to be taken. In which case, the recursion of the template could
        # also happen to the empty door of the template.
        if not self.__state_a_template_state_f:
            self.__state_a_recursion_to_empty_door_f = not self.__state_a.entry.door_has_commands(StateA.index, StateA.index)
        if not self.__state_b_template_state_f:
            self.__state_b_recursion_to_empty_door_f = not self.__state_b.entry.door_has_commands(StateB.index, StateB.index)

        if isinstance(StateA, TemplateState):
            if isinstance(StateB, TemplateState):
                self.get_target = self.get_target_TemplateState_TemplateState
            else:
                self.get_target = self.get_target_TemplateState_AnalyzerState
        else:
            if isinstance(StateB, TemplateState):
                self.get_target = self.get_target_AnalyzerState_TemplateState
            else:
                self.get_target = self.get_target_AnalyzerState_AnalyzerState
        
    def get_TargetScheme(self, SchemeA, SchemeB):
        """Checks whether the combination is already present. If so, the reference
           to the existing target scheme is returned. If not a new scheme is created
           and entered into the database.

           The Targets must be a tuple, such as 

              (1, E_StateIndices.DROP_OUT, 4, ...)

           which tells that if the template operates with

              -- state_key = 0 (first element) there must be a transition to state 1, 
              -- state_key = 1 (second element), then there must be a drop-out,
              -- state_key = 2 (third element), then transit to state 4,
              -- ...
        """
        assert isinstance(SchemeA, tuple)
        assert isinstance(SchemeB, tuple)

        scheme = SchemeA + SchemeB

        for target in scheme:
            assert isinstance(target, DoorID) or target == E_StateIndices.DROP_OUT 

        result = dict.get(self, scheme)
        if result is None: 
            new_index    = len(self)
            result       = TargetScheme(scheme, new_index)
            self[scheme] = result

        return result

    def get_scheme_list(self):
        return self.values()

    def get_target(self):
        """This function is designed as a function pointer which will point to 
           one of the following functions depending on the involved state classes:
               -> get_target_AnalyzerState_AnalyzerState()
               -> get_target_AnalyzerState_TemplateState()
               -> get_target_TemplateState_AnalyzerState()
               -> get_target_TemplateState_TemplateState()
        """
        assert False

    def get_target_AnalyzerState_AnalyzerState(self, TA, TB):
        # Since TA and TB come from an ordinary AnalyzerState
        # -- they cannot be a DoorID
        # -- they cannot be RECURSIVE
        # -- they cannot be a TargetScheme
        assert isinstance(TA, (int, long)) or TA == E_StateIndices.DROP_OUT
        assert isinstance(TB, (int, long)) or TB == E_StateIndices.DROP_OUT

        if TA == self.__state_a_index and self.__state_a_recursion_to_empty_door_f:
            if TB == self.__state_b_index and self.__state_b_recursion_to_empty_door_f:
                return TargetScheme(E_StateIndices.RECURSIVE) # uniform
            else:
                TA_door_id = self.__analyzer.state_db[TA].entry.get_door_id(TA, TA)

        elif   TA == E_StateIndices.DROP_OUT:
            if TB == E_StateIndices.DROP_OUT:
                return TargetScheme(E_StateIndices.DROP_OUT)  # uniform
            else:
                TA_door_id = E_StateIndices.DROP_OUT

        else:
            TA_door_id = self.__analyzer.state_db[TA].entry.get_door_id(TA, self.__state_a_index)

        # TB and TA cannot be recursive, otherwise we would have left above.

        if TB == E_StateIndices.DROP_OUT:
            # TA cannot be DROP_OUT, otherwise we would have left
            TB_door_id = E_StateIndices.DROP_OUT

        else:
            TB_door_id = self.__analyzer.state_db[TB].entry.get_door_id(TB, self.__state_b_index)

        if TA_door_id == TB_door_id:
            return TargetScheme(TA_door_id)               # uniform
        else:
            return self.get_TargetScheme((TA_door_id,), (TB_door_id,))

    def get_target_AnalyzerState_TemplateState(self, TA, TB):
        result = self.__get_target_AnalyzerState_TemplateState(TA, self.__state_a_index, 
                                                               self.__state_a_recursion_to_empty_door_f, 
                                                               TB, self.__state_b_state_index_list)
        if type(result) != tuple: return result
        return self.get_TargetScheme(result[0], result[1])

    def get_target_TemplateState_AnalyzerState(self, TA, TB):
        result = self.__get_target_AnalyzerState_TemplateState(TB, self.__state_b_index, 
                                                               self.__state_b_recursion_to_empty_door_f, 
                                                               TA, self.__state_a_state_index_list)
        if type(result) != tuple: return result
        return self.get_TargetScheme(result[1], result[0])

    def __get_target_AnalyzerState_TemplateState(self, T0, State0Index, State0RecursionToEmptyDoorF, 
                                                 T1, State1StateIndexList):
        # Since T0 comes from an ordinary AnalyzerState
        # -- T0 cannot be a DoorID
        # -- T0 cannot be RECURSIVE
        # -- T0 cannot be a TargetScheme
        assert    isinstance(T0, (int, long)) or T0 == E_StateIndices.DROP_OUT
        assert    isinstance(T1, TargetScheme) 

        if T1.recursive_f:
            if T0 == State0Index and State0RecursionToEmptyDoorF:
                return T1
            T1_scheme = self.__expand_recursive_target(State1StateIndexList)

        elif T1.drop_out_f:
            if T0 == E_StateIndices.DROP_OUT:
                return T1
            T1_scheme = (E_StateIndices.DROP_OUT,) * len(State1StateIndexList)

        elif T1.door_id is not None:
            if T0 != E_StateIndices.DROP_OUT:
                T0_door_id = self.__analyzer.state_db[T0].entry.get_door_id(T0, State0Index)
                if T0_door_id == T1.door_id: 
                    return T1
            T1_scheme = (T1.door_id,) * len(State1StateIndexList)

        else:
            # T1 is a tuple of doors
            T1_scheme = T1.scheme

        # T0 and T1 cannot be recursive, otherwise we would have left

        if T0 == E_StateIndices.DROP_OUT:
            # T1 cannot be DROP_OUT, otherwise we would have left already
            T0_door_id = E_StateIndices.DROP_OUT

        else:
            T0_door_id = self.__analyzer.state_db[T0].entry.get_door_id(T0, State0Index)

        T0_scheme  = (T0_door_id,) 

        return (T0_scheme, T1_scheme)

    def get_target_TemplateState_TemplateState(self, TA, TB):
        assert    isinstance(TA, (DoorID, TargetScheme)) \
               or TA == E_StateIndices.DROP_OUT          \
               or TA == E_StateIndices.RECURSIVE
        assert    isinstance(TB, (DoorID, TargetScheme)) \
               or TB == E_StateIndices.DROP_OUT          \
               or TB == E_StateIndices.RECURSIVE

        if TA.recursive_f:
            if TB.recursive_f:
                return TA
            TA_scheme = self.__expand_recursive_target(self.__state_b_state_index_list)

        elif TA.drop_out_f:
            if TB.drop_out_f:
                return TA
            TA_scheme = (E_StateIndices.DROP_OUT,) * self.__state_a_state_index_list_length

        elif TA.door_id is not None:
            if TB.door_id is not None and TA.scheme == TB.scheme:
                return TA
            TA_scheme = (TA.door_id,) * self.__state_a_state_index_list_length

        else:
            TA_scheme = TA.scheme

        if TB.recursive_f:
            # TA was not recursive, otherwise we would have returned earlier
            TB_scheme = self.__expand_recursive_target(self.__state_b_state_index_list)

        elif TB.drop_out_f:
            # TA was not drop-out, otherwise we would have returned earlier
            TB_scheme = (E_StateIndices.DROP_OUT,) * self.__state_b_state_index_list_length

        elif TB.door_id is not None:
            # TA was not the same door, otherwise we would have returned earlier
            TB_scheme = (TB.door_id,) * self.__state_b_state_index_list_length

        else:
            TB_scheme = TB.scheme

        return self.get_TargetScheme(TA_scheme, TB_scheme)

    def __expand_recursive_target(self, StateIndexList):
        # Expand the 'RECURSIVE' into a tuple of doors
        # Recursive entries always happen into the empty door 'Door 0' where
        # no actions are to be taken.
        return tuple(DoorID(state_index, 0) for state_index in StateIndexList)

def get_state_list(X): 
    if isinstance(X, TemplateState): return X.state_index_list 
    else:                            return [ X.index ]

def get_iterable(X, StateIndexList): 
    if isinstance(X, defaultdict): return X.iteritems()
    else:                          return [(X, StateIndexList)]

