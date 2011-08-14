from   quex.engine.interval_handling              import Interval
import quex.engine.state_machine.index            as index
import quex.engine.state_machine.core             as state_machine
from   quex.engine.analyzer.core                  import AnalyzerState
import quex.engine.analyzer.templates.gain        as templates_gain
import quex.engine.analyzer.template.combine_maps as combine_maps
from   quex.blackboard                            import TargetStateIndices

from   itertools import ifilter
from   operator  import itemgetter
from   copy      import copy
import sys

# (C) 2010 Frank-Rene Schaefer
"""
   Template Compression _______________________________________________________

   The idea behind 'template compression' is to combine the transition maps of
   multiple similar states into a single transition map. The difference in the
   transition maps are dealt with by an adaption table. For example the three
   states

         .---- 'a' --> 2        .---- 'a' --> 2        .---- 'a' --> 2
         |                      |                      |
       ( A )-- 'e' --> 0      ( B )-- 'e' --> 1      ( C )-- 'e' --> 2
         |                      |                      |
         `---- 'x' --> 5        `---- 'x' --> 5        `---- 'y' --> 5

   can be combined into a single template state

                         .----- 'a' --> 2 
                         |               
                      ( T1 )--- 'e' --> Target0 
                         |\               
                         \  `-- 'x' --> Target1
                          \
                           `--- 'y' --> Target2

   where the targets Target0, Target1, and Target2 are adapted. If the template
   has to mimik state A then Target0 needs to be 1, Target1 is 5, and Target2
   is 'drop-out'. The adaptions can be stored in a table:

                                A     B     C
                       Target0  0     1     2
                       Target1  5     5     drop
                       Target2  drop  drop  5

   Practically, this means that a 'goto state' is transformed into a 'set state
   key' plus a 'goto template'. The state key tells which column of the table
   is to be used in the transition map. Thus, a state that is implemented in a
   template is identified by 'template index' and 'state key', i.e.

            templated state <--> (template index, state key)

   The combination of multiple states reduces memory consumption. The
   efficiency increases with the similarity of the transition maps involved.
   The less differences there are in the trigger intervals, the less additional
   intervals need to be added. The less differences there are in target states,
   the less information needs to be stored in adaption tables.

   Result ______________________________________________________________________


   The result of analyzis of template state compression is:
    
              A list of 'TemplateCombination' objects. 

   A TemplateCombination carries:
   
     -- A trigger map, i.e. a list of intervals together with target state
        lists to which they trigger. If there is only one associated target
        state, this means that all involved states trigger to the same target
        state.

     -- A list of involved states. A state at position 'i' in the list has
        the state key 'i'. It is the key into the adaption table mentioned
        above.

   Algorithm __________________________________________________________________

   Not necessarily all states can be combined efficiently with each other. The
   following algorithm finds successively best combinations and stops when no
   further useful combinations can be found. 

   Each state has a transition map, i.e. an object that tells on what character
   code intervals the analyzer jump to what states:

             transition map:  interval  --> target state

   The algorithm works as follows:

      (1) Compute for each combination candidate of two states the 
          expected 'gain' if they were combined. This happens by 
          comparison of the transition maps.

      (2.a) Do not consider to combine states where the 'gain' is negative.

      (2.b) Take the pair of states that provide the highest gain.
            
            Create a TemplateCombination object based on the two states.

            Enter the TemplateCombination as a normal 'state' into the database.

            Goto (1)

   Measurement of the 'Gain Value' ____________________________________________

   The 'gain' shall **represent** the amount of memory that can be spared if
   two trigger maps are combined. The number does not necessarily relate
   directly to a physical byte consumption. It is only required, that
   if a combination of (A, B) spares more than a combination of (C, D) then
   the gain value of (A, B) must be greater than the gain value for (C, D).

   The measurement of 'gain' is done in two steps:

       (1) get_transition_map_metric(A, B): computes the number of borders of a
           transition map that would combine the two trigger
           maps A and B. Also, it combines the number of target
           set combinations, i.e. the number of X0, X1, X3 ...
           in the example above.

       (2) compute_combination_gain(...): computes a scalar value that indicates
           the 'gain' in terms of program space, if the two trigger
           maps are combined. This function is controlled by the
           coefficient 'CX' that indicates the ratio between the
           'normal cost' of transition and the cost of routing, i.e.
           entering the right target state according to the adapted
           trigger map.

   both functions work with normal state trigger maps and objects of class
   TemplateCombination.

   Class TemplateCombination __________________________________________________

   Combined trigger maps are stored in objects of type 'TemplateCombination'.
   As normal trigger maps they are built of a list of tuples:

              (I0, TL0),       # meaning interval I0 triggers to TL0
              (I1, TL1),       #                  I1 triggers to TL1
              .... 
              (In, TLn)        #                  In triggers to TLn

   where the intervals I0 to In are adjacent intervals starting with 

              I0.begin == - sys.maxint

   and ending with 

              In.end   == sys.maxint

   In 'normal trigger maps' the target state indices TL0 to TLn are scalar
   values. In a 'TemplateCombination' object, the 'target' can be a scalar
   value or a list. Accordingly, this means that TLk is

        a scalar, if Ik maps to the same target state for all involved 
                  states.

                  If TLk == TargetStateIndices.SAME_STATE, then all involved states
                  trigger recursively.

        a list, if Ik maps to different target states for each involved
                state. Then, Tlk[i] is the target state to which the 
                state with key 'i' triggers.  

   The state key has been mentioned above. It designates the column in the
   adaption table that is required for each state involved.

"""

def do(TheAnalyzer, CostCoefficient):
    """
       sm:              StateMachine object containing all states

                        NOTE: The init state is **never** part of a template 
                              combination.

       CostCoefficient: Coefficient that indicates how 'costy' it is differentiate
                        between target states when it is different in states that
                        are combined into a template. Meaningful range: 0 to 3.

       RETURNS: List of template combinations.
    """
    assert isinstance(CostCoefficient, (int, long, float))

    trigger_map_db = TriggerMapDB(TheAnalyzer, CostCoefficient)

    # Build templated combinations by finding best pairs, until there is no meaningful way to
    # build any clusters. TemplateCombinations of states also take part in the race.
    while 1 + 1 == 2:
        i, i_state, k, k_state = trigger_map_db.pop_best_matching_pair()
        if i is None: break

        # Add new element: The combined pair
        new_index = index.get()
        trigger_map_db[new_index] = TemplateState(new_index, i_state, k_state)

    result = []
    for state_index, combination in trigger_map_db.items():
        if isinstance(combination, TemplateCombination): result.append(combination)

    return result

class TemplateState(AnalyzerState):
    def __init__(self, Index, StateA, StateB):
        def get_state_list(X): 
            if   isinstance(X, AnalyzerState): return [ X.index ]
            elif isinstance(X, TemplateState): return X.state_index_list 
            else:                              assert False

        StateListA     = get_state_list(StateA)
        StateListB     = get_state_list(StateB)
        TransitionMapA = StateA.transition_map
        TransitionMapB = StateB.transition_map

        self.index            = Index
        self.entry            = EntryTemplate(StateA.entry, StateB.entry)
        self.drop_out         = DropOutTemplate(StateA.entry, StateB.entry)
        self.state_index_list = StateListA + StateListB
        # If the target of the transition map is a list for a given interval X, i.e.
        #
        #                           (X, target[i]) 
        # 
        # then this means that 
        #
        #      target[i] = target of state 'state_index_list[i]' for interval X.
        #
        self.transition_map   = combine_maps.do(StateListA, TransitionMapA, 
                                                StateListB, TransitionMapB)

class EntryTemplate(object):
    """State entry for TemplateState objects."""
    def __init__(self, StateIndexA, EntryA, StateIndexB, EntryB):
        self.scheme = get_combined_scheme(StateIndexA, EntryA, StateIndexB, EntryB, 
                                          EntryTemplate)

class DropOutTemplate(object):
    """State drop_out for TemplateState objects."""
    def __init__(self, StateIndexA, DropOutA, StateIndexB, DropOutB):
        self.scheme = get_combined_scheme(StateIndexA, DropOutA, StateIndexB, DropOutB, 
                                          DropOutTemplate)

def get_combined_scheme(StateIndexA, A, StateIndexB, B, Type):
    def get_scheme(StateIndex, X): 
        if isinstance(X, Type): return X.scheme
        else:                   return defaultdict([(X, [StateIndex])])

    scheme_a = get_scheme(StateIndexA, A)
    scheme_b = get_scheme(StateIndexB, B)

    result = defaultdict(list)
    for element, state_index_list in chain(scheme_a.iteritems(), scheme_b.iteritems()):
        result[element].extend(state_index_list)
    return result

class TemplateCombination:
    def __init__(self, InvolvedStateList0,  InvolvedStateList1):
        self.__trigger_map         = []
        self.__involved_state_list = InvolvedStateList0 + InvolvedStateList1

    def involved_state_list(self):
        return self.__involved_state_list

    def append(self, Begin, End, TargetStateIdxList):
        """TargetStateIdxList can be
        
            A list of (long) integers: List of targets where

                list[i] == target index of involved state number 'i'

            A scalar value:

                i)  > 0, then all involved states trigger to this same
                         target index.
                ii) == TargetStateIndices.SAME_STATE, then all involved states are 
                                         recursive.
        """
        self.__trigger_map.append([Interval(Begin, End), TargetStateIdxList])

    def __getitem__(self, Index):
        return self.__trigger_map[Index]

    def __len__(self):
        return len(self.__trigger_map)

    def __repr__(self):
        txt = []
        for trigger in self.__trigger_map:
            txt.append("[%i, %i) --> %s\n" % \
                       (trigger[0].begin, trigger[0].end, trigger[1]))
        return "".join(txt)

    def get_trigger_map(self):
        return self.__trigger_map

class TriggerMapDB:
    def __init__(self, TheAnalyzer, CostCoefficient):
        # (1) Get the trigger maps of all states of the state machine
        self.__db = dict([(state_index, state) for state_index, state in \
                                                   ifilter(lambda x: len(x[1].transition_map) != 0, 
                                                           TheAnalyzer.state_db.iteritems())])
        self.__cost_coefficient      = float(CostCoefficient)
        self.__init_state_index      = TheAnalyzer.init_state_index
        self.__combination_gain_list = self.__initial_combination_gain()

    def __initial_combination_gain(self):
        state_list = self.__db.values()
        L          = len(state_list)

        # Pre-allocate the result array to avoid frequent allocations
        #
        # NOTE: L * (L - 1) is always even, i.e. dividable by 2.
        #       (a) L even = k * 2:     -> k * 2 ( k * 2 - 1 )            = k * k * 4 - k * 2
        #                                = even - even = even
        #       (b) L odd  = k * 2 + 1: -> (k * 2 + 1) * ( k * 2 + 1 - 1) = k * k * 4 + k * 2
        #                                = even + even = even
        #       => division by two without remainder 
        MaxSize = (L * (L - 1)) / 2
        result  = [None] * MaxSize
        n       = 0
        for i, i_state in enumerate(state_list):
            if i_state.init_state_f: continue

            for k, k_state in enumerate(state_list[i+1:]):
                if k_state.init_state_f: continue

                combination_gain = templates_gain.do(i_state, k_state)
                if combination_gain > 0:
                    result[n] = (combination_gain, i_state.index, k_state.index)
                    n += 1

        if n != MaxSize:
            del result[n:]

        # Sort according to delta cost
        result.sort(key=itemgetter(0))
        return result

    def __adapt_combination_gain(self, NewState):
        """Adapt the delta cost list **before** adding the trigger map to __db!"""
        assert isinstance(NewTriggerMap, TemplateCombination)

        # Avoid extensive 'appends' by single allocation (see initial computation)
        MaxIncrease = (len(self.__db) - 1)
        n           = len(self.__combination_gain_list)
        MaxSize     = len(self.__combination_gain_list) + MaxIncrease
        self.__combination_gain_list.extend([None] * MaxIncrease)

        for state in self.__db.itervalues():
            if state.init_state_f: continue

            combination_gain  = templates_gain.do(NewState, state)

            if combination_gain > 0:
                self.__combination_gain_list[n] = (combination_gain, NewState.index, state.index)
                n += 1

        if n != MaxSize:
            del self.__combination_gain_list[n:]

        self.__combination_gain_list.sort(key=itemgetter(0))

    def pop_best_matching_pair(self):
        """Determines the two trigger maps that are closest to each
           other. The consideration includes the trigger maps of
           combined trigger maps. Thus this function supports the
           clustering of the best trigger maps into combined trigger
           maps.

           If no pair can be found with a gain > 0, then this function
           returns 'None, None'.
        """
        if len(self.__combination_gain_list) == 0: return (None, None, None, None)

        # (0) The entry with the highest gain is at the tail of the list.
        #     Element 0 contains the combination gain.
        #     Element 1 and 2 contain the state indices of the states to be combined
        info = self.__combination_gain_list.pop()
        i       = info[1]          # State Index A
        i_state = self.__db[i]     # State A
        k       = info[2]          # State Index B
        k_state = self.__db[k]     # State B

        # (1) Delete both states from the database: state-index  --> trigger_map

        # (2) Delete all entries from the 'combination gain' list that relate
        #     to the states 'i' and 'k'. They are no longer available.
        X = (i, k)
        L = len(self.__combination_gain_list)
        p = 0
        while p < L:
            entry = self.__combination_gain_list[p]
            # Does entry contain 'i' or 'k'? If so the subsequent entries are 
            # likely to contain them two. Combine the 'del' for the chunk of
            # adjacent entries.
            if entry[1] in X or entry[2] in X:
                # Determine the end of the region to be deleted
                q = p + 1
                while q < L:
                    entry = self.__combination_gain_list[q]
                    if entry[1] not in X and entry[2] not in X: break
                    q += 1
                del self.__combination_gain_list[p:q]
                L -= (q - p)
            else:
                p += 1

        return i_state, k_state

    def __len__(self):
        return len(self.__db)

    def __getitem__(self, Key):
        assert type(Key) == long
        return self.__db[Key]

    def __setitem__(self, Key, Value):
        assert type(Key) == long
        assert isinstance(Value, TemplateCombination)
        self.__adapt_combination_gain(Value)
        self.__db[Key] = Value

    def items(self):
        return self.__db.items()

def involved_state_list(TM, DefaultIfTriggerMapIsNotACombination):
    if isinstance(TM, TemplateCombination):
        return TM.involved_state_list()
    else:
        return [ DefaultIfTriggerMapIsNotACombination ]

