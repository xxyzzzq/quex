from   quex.engine.analyzer.mega_state.core               import PseudoMegaState
from   quex.engine.analyzer.mega_state.template.state     import TemplateState
from   quex.engine.analyzer.mega_state.template.candidate import TemplateStateCandidate
from   quex.blackboard import E_Compression
from   itertools       import ifilter, islice

# (C) 2010 Frank-Rene Schaefer
"""
   Template Compression _______________________________________________________

   The idea behind 'template compression' is to combine the transition maps of
   multiple similar states into a single transition map. The difference in the
   transition maps is dealt with by an adaption table. For example the three
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

   The columns in the table tell how the template behaves if it operates on
   behalf of a certain state--here A, B, and C. Practically, a state_key is
   associated with each state, e.g. 0 for state A, 1 for state B, and 2 for
   state C.  Thus, a state that is implemented in a template is identified by
   'template index' and 'state key', i.e.

            templated state <--> (template index, state_key)

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
   code the analyzer jump to what states:

             transition map:  interval  --> target state

   The algorithm works as follows:

      (1) Compute for each possible pair of states a TemplateStateCandidate. 

          (1.1) Compute the 'gain of combination' for candidate.

          (1.2) Do not consider to combine states where the 'gain' is 
                below MinGain.

          (1.3) Register the candidate in 'candidate_list'.

      (4) Pop best candidate from candidate_list. If no more reasonable
          candidates present, then stop.
            
      (5) With given candidate goto (1.1)

   The above algorithm is supported by TemplateStateCandidate being derived
   from TemplateState.

   Measurement of the 'Gain Value' ____________________________________________

   The measurement of the gain value happens inside a TemplateStateCandidate. 
   It is a function of the similarity of the states. In particular the entries, 
   the drop_outs and the transition map is considered. 

   Transition Map of a TemplateState __________________________________________

   The transition map of a template state is a list of (interval, target)
   tuples as it is in a normal AnalyzerState. In an AnalyzerState the target
   can only be a scalar value indicating the target state. The target object of
   a TemplateState, though, can be one of the following:

        E_StateIndices.RECURSIVE -- which means that the template recurses
                                    to itself.

        Scalar Value X           -- All states that are involved in the template
                                    trigger for the given interval to the same
                                    state given by 'X'.

        MegaState_Target T       -- which means that the target state depends 
                                    on the state_key. 'T[state_key]' tells the
                                    target state when the templates operates
                                    for a state given by 'state_key'.

"""
def do(TheAnalyzer, MinGain, CompressionType, 
       AvailableStateIndexList, MegaStateList):
    """RETURNS: List of TemplateState-s that were identified from states in
                TheAnalyzer.

       ALGORITHM: 

       The Process computes for all possible combinations of states A and
       B an object of class TemplateStateCandidate. That is a template state that
       represents the combination of A and B. By means of a call to '.combine_best()'
       the candidate with the highest expected gain replaces the two states that 
       it represents. This candidate enters the Process as any other state
       and candidates of combinations with other states are computed. In this sense
       the iteration of calls to '.combine_next()' happen until no meaningful
       combination of states can be identified.
    """
    assert CompressionType in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM)
    assert isinstance(MinGain, (int, long, float))

    # (*) The Combination Process
    #
    # Process: -- Keep track of possible combinations between states.
    #          -- Can determine best matching state candidates for combination.
    #          -- Replaces two combined states by TemplateState.
    #
    # (A 'state' in the above sense can also be a TemplateState)
    combiner = Process(TheAnalyzer, MinGain, CompressionType, AvailableStateIndexList)

    # Combine states until there is nothing that can reasonably be combined.
    while combiner.combine_best():
        pass

    return combiner.result()

class Process:
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

       (1) .__candidate_list_construct(): The 'matrix' is first computed for all states.

       (2) .pop_best(): When the best pair is popped, the correspondent 
                        entries are deleted from the 'matrix'.
       (3) .enter(): The combined states is then entered. The gains for
                     combination with the other states in the 'matrix' 
                     is computed.
    """
    def __init__(self, TheAnalyzer, MinGain, CompressionType, AvailableStateIndexList):
        assert CompressionType in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM)
        assert MinGain >= 0
        self.__uniformity_required_f = (CompressionType == E_Compression.TEMPLATE_UNIFORM)
        self.__min_gain    = float(MinGain)

        # NOTE: States in '__elect_db' cannot be candidates listed in '__candidate_list'
        #       and vice versa. Candidates in '__candidate_list' combine two elects from
        #       '__elect_db' and the best candidates become elements of '__elect_db'.
        self.__elect_db = Process.__elect_db_construct(TheAnalyzer.state_db, 
                                                       AvailableStateIndexList)
        self.__candidate_list = self.__candidate_list_construct()
        self.__door_id_replacement_db = {}

    @staticmethod
    def __elect_db_construct(StateDB, AvailableStateIndexList):
        """Elect Database:
        
           Collects states which have been filtered out to be part of the final 
           state machine. The content of the elect database changes during the 
           process of TemplateState-finding. On the event of adding electing a
           new combination:
           
            -- The elected candidate, which combines two states (possibly
               already TemplateState) is entered into the '__elect_db'.
            -- The two states which the elect combines (and all states
               state they implement) must be deleted from the '__elect_db'.
        
           At the beginning all AnalyzerState-s are elected (and they remain
           elected if they cannot be efficiently combined). However, some 
           states may not be considered as they are:
        
           Do not consider: -- states with empty transition maps
                            -- states which are no more availabe for combination
                            -- the init state.
        """
        # x[0] = state_index, x[1] = state
        condition = lambda x:     x[0] in AvailableStateIndexList \
                              and len(x[1].transition_map) != 0   \
                              and x[1].init_state_f == False

        # Represent AnalyzerState-s by PseudoMegaState-s so they behave
        # uniformly with TemplateState-s.
        elect_db = dict((state_index, PseudoMegaState(state)) \
                        for state_index, state in ifilter(condition, StateDB.iteritems()) )

        return elect_db

    def __candidate_list_construct(self):
        """Compute TemplateStateCandidate-s for each possible combination of 
           two states in the '__elect_db'. If the gain of a combination is less 
           that 'self.__min_gain' then it is not considered.
        """
        state_list = self.__elect_db.values()
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

                if self.__uniformity_required_f:
                    # Rely on __eq__ operator (used '=='). '!=' uses __neq__ 
                    if   not (i_state.drop_out == k_state.drop_out):    continue
                    elif not (i_state.entry.is_uniform(k_state.entry)): continue

                candidate = TemplateStateCandidate(i_state, k_state)

                if candidate.gain >= self.__min_gain:
                    result[n] = (i_state.index, k_state.index, candidate)
                    n += 1
                else:
                    # Mention the states for which the other does not combine properly
                    i_state.bad_company_add(k_state.index)
                    k_state.bad_company_add(i_state.index)

        if n != MaxSize:
            del result[n:]

        # Sort according to delta cost
        result.sort(key=lambda x: x[2].gain) # 'best' must be at end
        return result

    def enter(self, NewElect):
        """Adapt the __candidate_list to include candidates of combinations with
           the NewElect.
        """
        assert isinstance(NewElect, TemplateStateCandidate)
        # The new state index must be known. It is used in the gain matrix.
        # But, the new state does not need to be entered into the db, yet.

        newcomer    = TemplateState(NewElect)
        # Avoid extensive 'appends' by single allocation (see initial computation)
        MaxIncrease = len(self.__elect_db) 
        n           = len(self.__candidate_list)
        MaxSize     = len(self.__candidate_list) + MaxIncrease
        self.__candidate_list.extend([None] * MaxIncrease)
        ImplementedStateIndexList = set(newcomer.implemented_state_index_list())

        for state in self.__elect_db.itervalues():
            if self.__uniformity_required_f:
                # Rely on __eq__ operator (used '=='). '!=' uses __neq__ 
                if   not (state.drop_out == newcomer.drop_out):    continue
                elif not (state.entry.is_uniform(newcomer.entry)): continue

            # Do not try to combine states that have proven to be 'bad_company'.
            if       state.index in newcomer.bad_company():                                   continue
            elif not newcomer.bad_company().isdisjoint(state.implemented_state_index_list()): continue
            elif not state.bad_company().isdisjoint(ImplementedStateIndexList):             continue
            # IMPOSSIBLE: newcomer.index in state.bad_company() 
            #             because when 'state' was created, 'newcomer' did not exist.
            candidate = TemplateStateCandidate(newcomer, state)

            if candidate.gain >= self.__min_gain:
                self.__candidate_list[n] = (state.index, newcomer.index, candidate)
                n += 1
            else:
                # Mention the states for which the other does not combine properly
                state.bad_company_add(newcomer.index)
                newcomer.bad_company_add(state.index)

        if n != MaxSize:
            del self.__candidate_list[n:]

        self.__candidate_list.sort(key=lambda x: x[2].gain) # 'best' must be at end

        self.__elect_db[newcomer.index] = newcomer

    def combine_best(self):
        """Finds the two best matching states and combines them into one.
           If no adequate state pair can be found 'False' is returned.
           Else, 'True'.
        """
        elect = self.pop_best()
        if elect is None: return False

        # The 'candidate' is a TemplateStateCandidate which is derived from 
        # TemplateState. Thus, it can play the TemplateState role without
        # modification. Only, a meaningful index has to be assigned to it.
        self.enter(elect)
        return True

    def result(self):
        """RETURNS: Map from 'absorbed AnalyzerState' indices to the Template state 
                    which implements it.
        """
        result = {}
        for state in (x for x in self.__elect_db.itervalues() if isinstance(x, TemplateState)):
            state.entry.door_tree_configure()
            result.update((i, state) for i in state.implemented_state_index_list())

        return result

    @property
    def candidate_list(self):
        return self.__candidate_list

    def pop_best(self):
        """Determines the two states that result in the greatest gain if they are 
           combined into a TemplateState. 

           If no combination has a "gain >= self.__min_gain", then None
           is returned. This is ensured, by not letting any entry enter the
           __candidate_list, where 'gain < self.__min_gain'.

           RETURNS: TemplateStateCandidate of combination of states with the 
                    greatest gain. 
                    None, if there is no more.
        """

        if len(self.__candidate_list) == 0: return None

        # (*) The entry with the highest gain is at the tail of the list.
        i, k, elect = self.__candidate_list.pop()

        # (*) __elect_db:    Remove 'i' and 'k' from '__elect_db'.
        #     __candidate_list: Remove any TemplateStateCandidate that combines 
        #                    'i' or 'k'. States have been implemented. No
        #                    other candidate has a chance.
        # 
        # If 'i' or 'k' refere to an AnalyzerState, then any combination where 'i'
        # or 'k' is involved is removed from the __candidate_list. The 'elect', let it 
        # have state index 'p', is the only state that contains now 'i' and 'k'. Any
        # state, with index 'q', that combines with it does not contain 'i' and 
        # 'k'. And, on the event of combining 'p' and other 'q' all other combinations
        # related to 'p' are deleted, thus all other combinations that contain
        # 'i' and 'k' are impossible.
        # => The consideration of 'implemented_state_index_list' is not necessary.
        self.__candidate_list_delete_references(i, k)
        del self.__elect_db[i]
        del self.__elect_db[k]

        return elect

    def __candidate_list_delete_references(self, I, K):
        """Delete all related entries in the '__candidate_list' that relate to states
           I and K. This function is used after the decision has been made that 
           I and K are combined into a TemplateState. None of them can be combined
           with another state anymore.
        """
        size = len(self.__candidate_list)
        i    = 0
        while i < size:
            entry = self.__candidate_list[i]
            if entry[0] == I or entry[0] == K or entry[1] == I or entry[1] == K:
                del self.__candidate_list[i]
                size -= 1
            else:
                i += 1

        return 

    def __len__(self):
        return len(self.__elect_db)

    def __getitem__(self, Key):
        assert False # This function should not be used, actually
        assert type(Key) == long
        return self.__elect_db[Key]

    def iteritems(self):
        for x in self.__elect_db.iteritems():
            yield x

