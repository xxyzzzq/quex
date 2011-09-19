import quex.engine.state_machine.index         as     index
import quex.engine.state_machine.core          as     state_machine
from   quex.engine.analyzer.template.state     import TemplateState
from   quex.engine.analyzer.template.candidate import TemplateStateCandidate
from   quex.blackboard                         import E_StateIndices

from   collections import defaultdict
from   itertools   import ifilter, chain, islice
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
    """RETURNS: List of TemplateState-s that were identified from states in
                TheAnalyzer.

       ALGORITHM: 

       The CombinationDB computes for all possible combinations of states A and
       B an object of class TemplateStateCandidate. That is a template state that
       represents the combination of A and B. By means of a call to '.combine_best()'
       the candidate with the highest expected gain replaces the two states that 
       it represents. This candidate enters the CombinationDB as any other state
       and candidates of combinations with other states are computed. In this sense
       the iteration of calls to '.combine_next()' happen until no meaningful
       combination of states can be identified.
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
    def __init__(self, TheAnalyzer, MinGain):
        assert MinGain >= 0
        # Database of states that are subject to combination tries.
        # The init state and states without transition map are excluded.
        self.__db = dict(ifilter(lambda x:     len(x[1].transition_map) != 0 
                                           and not x[1].init_state_f,
                                 TheAnalyzer.state_db.iteritems()))
        self.__analyzer    = TheAnalyzer
        self.__min_gain    = float(MinGain)
        self.__gain_matrix = self.__base()

    def combine_best(self):
        """Finds the two best matching states and combines them into one.
           If no adequate state pair can be found 'False' is returned.
           Else, 'True'.
        """
        candidate = self.pop_best()
        if candidate is None: return False

        # The 'candidate' is a TemplateStateCandidate which is derived from 
        # TemplateState. Thus, it can play the TemplateState role without
        # modification. Only, a meaningful index has to be assigned to it.
        self.enter(candidate)
        return True

    def result(self):
        """RETURNS: List of TemplateStates. Those are the states that have been 
                    generated from combinations of analyzer states.
        """
        return filter(lambda x: isinstance(x, TemplateState), self.__db.itervalues())

    @property
    def gain_matrix(self):
        return self.__gain_matrix

    def __base(self):
        """Compute TemplateStateCandidate-s for each possible combination of 
           two states in the StateDB. If the gain of a combination is less 
           that 'self.__min_gain' then it is not considered.
        """
        state_list = self.__db.values()
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
            for k_state in islice(state_list, i + 1, None):

                candidate = TemplateStateCandidate(i_state, k_state, self.__analyzer)

                if candidate.gain >= self.__min_gain:
                    result[n] = (i_state.index, k_state.index, candidate)
                    n += 1

        if n != MaxSize:
            del result[n:]

        # Sort according to delta cost
        result.sort(key=lambda x: x[2].gain)
        return result

    def enter(self, NewState):
        """Adapt the __gain_matrix to include candidates of combinations with
           the NewState.
        """
        assert isinstance(NewState, TemplateState)
        # The new state index must be known. It is used in the gain matrix.
        # But, the new state does not need to be entered into the db, yet.
        NewState.set_index(index.get())

        # Avoid extensive 'appends' by single allocation (see initial computation)
        MaxIncrease = len(self.__db) 
        n           = len(self.__gain_matrix)
        MaxSize     = len(self.__gain_matrix) + MaxIncrease
        self.__gain_matrix.extend([None] * MaxIncrease)

        for state in self.__db.itervalues():
            candidate = TemplateStateCandidate(NewState, state, self.__analyzer)

            if candidate.gain >= self.__min_gain:
                self.__gain_matrix[n] = (state.index, NewState.index, candidate)
                n += 1

        if n != MaxSize:
            del self.__gain_matrix[n:]

        self.__gain_matrix.sort(key=lambda x: x[2].gain)

        self.__db[NewState.index] = NewState

    def pop_best(self):
        """Determines the two states that result in the greatest gain if they are 
           combined into a TemplateState. 

           If no combination has a "gain >= self.__min_gain", then None
           is returned. This is ensured, by not letting any entry enter the
           __gain_matrix, where 'gain < self.__min_gain'.

           RETURNS: TemplateStateCandidate of combination of states with the 
                    greatest gain. 
                    None, if there is no more.
        """

        if len(self.__gain_matrix) == 0: return None

        # The entry with the highest gain is at the tail of the list.
        i, k, candidate = self.__gain_matrix.pop()

        # Delete related entries in __gain_matrix and database 
        self.__gain_matrix_delete(i)
        self.__gain_matrix_delete(k)

        # If the following fails, it means that states have been combined twice
        del self.__db[i]
        del self.__db[k]

        return candidate

    def __gain_matrix_delete(self, StateIndex):
        """Delete all related entries in the '__gain_matrix' that relate to states
           I and K. This function is used after the decision has been made that 
           I and K are combined into a TemplateState. None of them can be combined
           with another state anymore.
        """
        size = len(self.__gain_matrix)
        i    = 0
        while i < size:
            entry = self.__gain_matrix[i]
            if entry[0] == StateIndex or entry[1] == StateIndex:
                del self.__gain_matrix[i]
                size -= 1
            else:
                i += 1

        return 

    def __len__(self):
        return len(self.__db)

    def __getitem__(self, Key):
        assert False # This function should not be used, actually
        assert type(Key) == long
        return self.__db[Key]

    def iteritems(self):
        for x in self.__db.iteritems():
            yield x


