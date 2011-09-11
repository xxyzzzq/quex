import quex.engine.state_machine.index            as     index
import quex.engine.state_machine.core             as     state_machine
import quex.engine.analyzer.template.gain         as     templates_gain
from   quex.engine.analyzer.template.common       import get_state_list, TemplateState
from   quex.blackboard                            import E_StateIndices

from   collections import defaultdict
from   itertools   import ifilter, chain
from   operator    import itemgetter
from   copy        import copy
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
    
              A list of 'TemplateState' objects. 

   A TemplateState carries:
   
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

                  If TLk == E_StateIndices.RECURSIVE, then all involved states
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

       RETURNS: List of TemplateStates
    """
    assert isinstance(CostCoefficient, (int, long, float))

    # CombinationDB: -- Keep track of possible combinations between states.
    #                -- Can determine best matching state candidates for combination.
    #                -- Replaces two combined states by TemplateState.
    #
    # (A 'state' in the above sense can also be a TemplateState)
    combiner = CombinationDB(TheAnalyzer, CostCoefficient)

    # Combine states until there is nothing that can be reasonably be combined.
    while combiner.combine_best():
        pass

    return combiner.result()

class CombinationDB:
    """Contains the 'Gain' for each possible combination of states. This includes
       TemplateStates which are already combined. States are referred by state
       index. Internally, a list is maintained that stores for each possible 
       combination the gain. This list is sorted, so that a simple '.pop()' returns
       the best gain, and the two state indices that would need to be combined. 

       The 'matrix' is not actually a matrix. But, the name shall indicate that 
       the gain is computed for each possible pair as it could be nicely displayed
       in a matrix, e.g.

                       0     1    2     4
                  0    0   -4.0  2.1   7.1      The matrix is, of course, 
                  1          0  -0.8   2.1      symmetric.
                  2               0    1.2
                  4                     0

       (1) .__base(): The 'matrix' is first computed for all states.

       (2) .pop_best_pair(): When the best pair is popped, the correspondent 
                             entries are deleted from the 'matrix'.
       (3) .enter(): The combined states is then entered. The gains for
                     combination with the other states in the 'matrix' 
                     is computed.
    """
    def __init__(self, TheAnalyzer, CostCoefficient):
        # (1) Get the trigger maps of all states of the state machine
        #     (Never template the init state, never template states without transition map)
        self.__db = dict([(state_index, state) 
                          for state_index, state in 
                              ifilter(lambda x:     len(x[1].transition_map) != 0 
                                                and x[1].index != Analyzer.init_state_index,
                                      TheAnalyzer.state_db.iteritems())
                         ])
        self.__cost_coefficient = float(CostCoefficient)
        self.__gain_matrix      = self.__base()

    def combine_best(self):
        """Finds the two best matching states and combines them into one.
           If no adequate state pair can be found 'False' is returned.
           Else, 'True'.
        """
        # Get the two best matching state candidates
        i, k = self.pop_best_pair()
        if i is None: return False

        # Combine the two
        new_index = index.get()
        new_state = TemplateState(new_index, self.__db[i], self.__db[k])

        self.enter(new_state)
        return True

    def result(self):
        """RETURNS: List of TemplateStates. Those are the states that have been 
                    generated from combinations of analyzer states.
        """
        return filter(lambda x: isinstance(x, TemplateState), self.itervalues())

    def __base(self, StateDB):
        state_list = StateDB.values()
        L          = len(state_list)

        # Pre-allocate the result array to avoid frequent allocations
        #
        # NOTE: L * (L - 1) is always even, i.e. dividable by 2.
        #       Proof:
        #       (a) L even = k * 2:     -> k * 2 ( k * 2 - 1 )            = k * k * 4 - k * 2
        #                                = even - even = even
        #       (b) L odd  = k * 2 + 1: -> (k * 2 + 1) * ( k * 2 + 1 - 1) = k * k * 4 + k * 2
        #                                = even + even = even
        # 
        #       => division by two without remainder 
        MaxSize = (L * (L - 1)) / 2
        result  = [None] * MaxSize
        n       = 0
        for i, i_state in enumerate(state_list):
            if i_state.init_state_f: continue

            for k_state in islice(state_list, i + 1, None):
                if k_state.init_state_f: continue

                candidate = TemplateStateCandidate(i_state, k_state)
                if candidate.gain > 0:
                    result[n] = candidate
                    n += 1

        if n != MaxSize:
            del result[n:]

        # Sort according to delta cost
        result.sort(key=itemgetter(0))
        return result

    def enter(self, NewState):
        """Adapt the delta cost list **before** adding the trigger map to __db!"""
        assert isinstance(NewState, TemplateState)

        # Avoid extensive 'appends' by single allocation (see initial computation)
        MaxIncrease = (len(self.__db) - 1)
        n           = len(self.__gain_matrix)
        MaxSize     = len(self.__gain_matrix) + MaxIncrease
        self.__gain_matrix.extend([None] * MaxIncrease)

        for state in self.__db.itervalues():
            if state.init_state_f: continue

            candidate = TemplateStateCandidate(NewState, state)

            if candidate.gain > 0:
                self.__gain_matrix[n] = candidate
                n += 1

        if n != MaxSize:
            del self.__gain_matrix[n:]

        self.__gain_matrix.sort(key=itemgetter(0))
        self.__db[new_index] = new_state

    def pop_best_pair(self):
        """Determines the two trigger maps that are closest to each
           other. The consideration includes the trigger maps of
           combined trigger maps. Thus this function supports the
           clustering of the best trigger maps into combined trigger
           maps.

           If no pair can be found with a gain > 0, then this function
           returns 'None, None'.

           RETURNS: (state_index_a, state_index_b) of the best matching
                    pair that was registered in the matrix.
        """
        if len(self.__gain_matrix) == 0: return (None, None)

        # (0) The entry with the highest gain is at the tail of the list.
        #     Element 0 contains the combination gain.
        #     Element 1 and 2 contain the state indices of the states to be combined
        i, k = self.__gain_matrix.pop()
        self.__delete_pair(i, k)
        return i, k

    def __get_combination_candidate(self, I, K):

    def __delete_pair(self, I, K):
        # (1) Delete both states from the database: state-index  --> trigger_map
        # (2) Delete all entries from the 'combination gain' list that relate
        #     to the states 'i' and 'k'. They are no longer available.
        X = (I, K)
        L = len(self.__gain_matrix)
        p = 0
        while p < L:
            entry = self.__gain_matrix[p]
            # Does entry contain 'i' or 'k'? If so the subsequent entries are 
            # likely to contain them two. Combine the 'del' for the chunk of
            # adjacent entries.
            if entry[1] in X or entry[2] in X:
                # Determine the end of the region to be deleted
                q = p + 1
                while q < L:
                    entry = self.__gain_matrix[q]
                    if entry[1] not in X and entry[2] not in X: break
                    q += 1
                del self.__gain_matrix[p:q]
                L -= (q - p)
            else:
                p += 1

        return i, k

    def __len__(self):
        return len(self.__db)

    def __getitem__(self, Key):
        assert False # This function should not be used, actually
        assert type(Key) == long
        return self.__db[Key]

    def iteritems(self):
        for x in self.__db.iteritems():
            yield x


