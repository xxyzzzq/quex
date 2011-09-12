from quex.engine.analyzer.core import AnalyzerState

class TemplateState(AnalyzerState):
    """A TemplateState is a state that is implemented by as a function of two
       similar states. The similarity is measured in terms of their transition 
       maps, their entry and drop_out behavior. 

       The idea between a TemplateState is that it implements the general scheme
       of both states once, and keeps track of the minor particularities. For
       details about how this is done, consider 'combine_maps.do(...)'. The 
       combination of entry and drop out behaviors happens inside the '__init__(...)'
       functions of EntryTemplate and DropOutTemplate.

       TemplateStates function based on 'state_keys'. Those state keys are used
       as indices into TemplateTargetSchemes. The 'state_key' of a given state 
       relates to the 'state_index' by

            (1)    self.state_index_list[state_key] == state_index

       where 'state_index' is the number by which the state is identified inside
       its state machine. Correspondingly, for a given TemplateTargetSchemes T 

            (2)                   T[state_key]

       gives the target of the template if it operates for 'state_index' determined
       from 'state_key' by relation (1). The state index list approach facilitates
       the computation of target schemes. For this reason no dictionary {state_index->target}
       is used.

       EntryTemplate and DropOutTemplate refer to the state by the original 'state_index'.
    """
    def __init__(self, StateA, StateB):
        StateListA     = get_state_list(StateA)
        StateListB     = get_state_list(StateB)
        TransitionMapA = StateA.transition_map
        TransitionMapB = StateB.transition_map

        # The 'index' remains None, as long as the TemplateState is not an 
        # accepted element of a state machine. This makes sense, in particular
        # for TemplateStateCandidates (derived from TemplateState). 
        self.__index          = None
        self.entry            = get_combined_scheme(StateA.entry, StateB.entry)
        self.drop_out         = get_combined_scheme(StateA.drop_out, StateB.drop_out)
        self.state_index_list = StateListA + StateListB
        # If the target of the transition map is a list for a given interval X, i.e.
        #
        #                           (X, target[i]) 
        # 
        # then this means that 
        #
        #      target[i] = target of state 'state_index_list[i]' for interval X.
        #
        self.transition_map = combine_maps.do(StateA, StateB)

    def set_index(self, Value):
        self.__index = Value

    @property
    def index(self):
        # A non-accepted state should never be asked about its index
        assert self.__index is not None
        return self.__index

def get_combined_scheme(StateIndexA, A, StateIndexB, B):
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
    A_iterable = get_iterable(A, StateIndexA)
    B_iterable = get_iterable(B, StateIndexA)

    result = defaultdict(list)
    for element, state_index_list in chain(A_iterable, B_iterable):
        assert hasattr(element, "__hash__")
        assert hasattr(element, "__eq__")
        result[element].extend(state_index_list)
    return result

def get_state_list(X): 
    if isinstance(X, TemplateState): return X.state_index_list 
    else:                            return [ X.index ]

def get_iterable(X, StateIndex): 
    if isinstance(X, defaultdict): return X.iteritems()
    else:                          return [(X, StateIndex)]

