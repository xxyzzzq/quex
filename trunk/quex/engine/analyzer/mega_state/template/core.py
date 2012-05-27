from   quex.engine.analyzer.mega_state.core               import PseudoMegaState
from   quex.engine.analyzer.mega_state.template.state     import TemplateState
from   quex.engine.analyzer.mega_state.template.candidate import TemplateStateCandidate
from   quex.engine.analyzer.state.entry_action       import DoorID
from   quex.blackboard import E_Compression, E_StateIndices
from   itertools       import ifilter, islice
from   collections     import defaultdict
from   copy            import copy

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

          (1.3) Register the candidate in 'gain_matrix'.

      (4) Pop best candidate from gain_matrix. If no more reasonable
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

       The CombinationDB computes for all possible combinations of states A and
       B an object of class TemplateStateCandidate. That is a template state that
       represents the combination of A and B. By means of a call to '.combine_best()'
       the candidate with the highest expected gain replaces the two states that 
       it represents. This candidate enters the CombinationDB as any other state
       and candidates of combinations with other states are computed. In this sense
       the iteration of calls to '.combine_next()' happen until no meaningful
       combination of states can be identified.
    """
    assert CompressionType in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM)
    assert isinstance(MinGain, (int, long, float))

    # (*) The Combination Process
    #
    # CombinationDB: -- Keep track of possible combinations between states.
    #                -- Can determine best matching state candidates for combination.
    #                -- Replaces two combined states by TemplateState.
    #
    # (A 'state' in the above sense can also be a TemplateState)
    combiner = CombinationDB(TheAnalyzer, MinGain, CompressionType, AvailableStateIndexList)

    # Combine states until there is nothing that can be reasonably be combined.
    while combiner.combine_best():
        pass

    done_state_index_set, template_state_list = combiner.result()

    ## print "##RESULT:", done_state_index_set
    ## print "         ", len(template_state_list), [x.index for x in template_state_list]
    return done_state_index_set, template_state_list

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
        self.__elect_db,      \
        self.__all_db         = self.__elect_db_construct(TheAnalyzer.state_db, 
                                                          AvailableStateIndexList)
        self.__candidate_list = self.__candidate_list_construct()
        self.__door_id_replacement_db = {}

    def __elect_db_construct(self, StateDB, AvailableStateIndexList):
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
        condition = lambda x:     len(x[1].transition_map) != 0 \
                              and x[0] in AvailableStateIndexList \
                              and x[1].init_state_f == False

        # state = self.__analyzer.state_db[358]
        # print "##transition_map (358): {"
        # for key, value in state.transition_map:
        #     print "## %s --> %s" % (key.get_string(Option="hex"), value)
        # print "##}"
        # state = self.__analyzer.state_db[350]
        # print "##transition_db (350): {"
        # for key, value in state.entry.transition_db.iteritems():
        #     print "## %s --> %s" % (key, value)
        # print "##}"

        # Represent AnalyzerState-s by PseudoMegaState-s so they behave
        # uniformly with TemplateState-s.
        elect_db = dict((state_index, PseudoMegaState(state)) \
                        for state_index, state in ifilter(condition, StateDB.iteritems()) )
        all_db   = dict(StateDB)
        all_db.update(elect_db)

        # The door_db and transition_db may have changed. The transition map can
        # only be adapted after all database are constructed. 
        for state in elect_db.itervalues():
            state.transition_map_construct(all_db)

        return elect_db, all_db

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

                candidate = TemplateStateCandidate(i_state, k_state, self.__all_db)

                if candidate.gain >= self.__min_gain:
                    result[n] = (i_state.index, k_state.index, candidate)
                    n += 1

        if n != MaxSize:
            del result[n:]

        # Sort according to delta cost
        result.sort(key=lambda x: x[2].gain)
        return result

    def enter(self, NewElect):
        """Adapt the __candidate_list to include candidates of combinations with
           the NewElect.
        """
        assert isinstance(NewElect, TemplateState)
        # The new state index must be known. It is used in the gain matrix.
        # But, the new state does not need to be entered into the db, yet.

        # Avoid extensive 'appends' by single allocation (see initial computation)
        MaxIncrease = len(self.__elect_db) 
        n           = len(self.__candidate_list)
        MaxSize     = len(self.__candidate_list) + MaxIncrease
        self.__candidate_list.extend([None] * MaxIncrease)

        NewElect.replace_door_ids_in_transition_map(self.__door_id_replacement_db)
        self.__assert_transition_map(NewElect)
        for state in self.__elect_db.itervalues():
            if self.__uniformity_required_f:
                # Rely on __eq__ operator (used '=='). '!=' uses __neq__ 
                if   not (state.drop_out == NewElect.drop_out):    continue
                elif not (state.entry.is_uniform(NewElect.entry)): continue

            state.replace_door_ids_in_transition_map(self.__door_id_replacement_db)
            self.__assert_transition_map(state)
            candidate = TemplateStateCandidate(NewElect, state, self.__all_db)

            if candidate.gain >= self.__min_gain:
                self.__candidate_list[n] = (state.index, NewElect.index, candidate)
                n += 1

        if n != MaxSize:
            del self.__candidate_list[n:]

        self.__candidate_list.sort(key=lambda x: x[2].gain)

        self.__elect_db[NewElect.index] = NewElect


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

    def result_iterable(self):
        """RETURNS: List of TemplateStates. Those are the states that have been 
                    generated from combinations of analyzer states.
        """
        return ifilter(lambda x: isinstance(x, TemplateState), self.__elect_db.itervalues())

    def result(self):
        """RETURNS: List of TemplateStates. Those are the states that have been 
                    generated from combinations of analyzer states.
        """
        template_state_list = [x for x in self.__elect_db.itervalues() if isinstance(x, TemplateState)]
        done_state_index_set = set()
        for state in template_state_list:
            done_state_index_set.update(state.state_index_list)
            state.target_scheme_list_update(self.__door_id_replacement_db)
            #if state.index == 2374:
                #print "##transition_map: {"
                #for key, value in state.transition_map:
                #    print "## %s --> %s" % (key.get_string(Option="hex"), value)
                #print "##}"
                

        #state = self.__analyzer.state_db[350]
        #print "##AFTER: transition_db (350): {"
        #for key, value in state.entry.transition_db.iteritems():
        #    print "## %s --> %s" % (key, value)
        #print "##}"
        #print "##AFTER: door_db (350): {"
        #for key, value in state.entry.door_db.iteritems():
        #    print "## %s --> %s" % (key, value)
        #print "##}"
        #print "##door_id_replacement_db: {"
        #for key, value in sorted(self.__door_id_replacement_db.iteritems()):
        #    print "## %s --> %s" % (key, value)
        #print "##}"

        return done_state_index_set, template_state_list

    @property
    def gain_matrix(self):
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

        # print "##ELECT:", elect.index,  elect._DEBUG_combined_state_indices()
        # print "##     :", self.__door_id_replacement_db

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

        # -- Extend the 'door_id_replacement_db' by what has been implemented in 'elect'
        self.__door_id_replacement_db.update(elect.entry.door_id_replacement_db)
        self.__door_id_replacement_db.update(elect.door_id_update_db)

        #print "##121,2 --> ", self.__door_id_replacement_db.get(DoorID(121L, 2))
        #if elect.index == 121:
        #    for interval, target in elect.transition_map:
        #        print "##", target

        # -- All previous replacements from 'i' and 'k' must be replaced
        #    by DoorID-s from 'elect'.
        for original, replacement in self.__door_id_replacement_db.items():
            if    replacement.state_index == i \
               or replacement.state_index == k: 
                # Get a more recent replacement for 'original'
                self.__door_id_replacement_db[original] = elect.door_id_update_db[replacement]

        ## -- All states that may be potentially combined must have their
        ##    transition maps adapted.
        #for state in self.__elect_db.itervalues():
        #    state.replace_door_ids_in_transition_map(self.__door_id_replacement_db)

        # -- The implemented states must give the right 'advice'
        for state_index in elect.implemented_state_index_list():
            original         = self.__all_db[state_index] 
            original_door_db = original.entry.door_db
            t_db = defaultdict(list)
            d_db = {}
            for door_id, transition_id_list in elect.entry.transition_db.iteritems():
                concerned_list = [ transition_id for transition_id in transition_id_list \
                                   if original_door_db.has_key(transition_id) ]
                if len(concerned_list) == 0:
                    continue
                t_db[door_id] = concerned_list
                d_db.update((transition_id, door_id) for transition_id in concerned_list)   
                   
            original.entry.set_transition_db(t_db)
            original.entry.set_door_db(d_db)

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

    def __DEBUG_checks(self):
        # CHECKS
        original_set    = set(self.__door_id_replacement_db.iterkeys())
        replacement_set = set(self.__door_id_replacement_db.itervalues())
        if not original_set.isdisjoint(replacement_set): 
            # print "##", self.__door_id_replacement_db
            # for x in original_set.intersection(replacement_set):
            #     print "##", x, "-->", self.__door_id_replacement_db[x]
            #     for p, q in self.__door_id_replacement_db.iteritems():
            #         if q == x: print "##", p, "-->", q
            assert False

        # -- The 'replacement' doors must all be in '__elect_db' states.
        # -- The root door of a TemplateState can not be targetted directly
        #    from outside (state key must be set).
        for door_id in replacement_set:
            state = self.__elect_db.get(door_id.state_index)
            if state is None and door_id.state_index == elect.index:
                state = elect
            assert state is not None
            if door_id.door_index == 0:
                assert isinstance(state, TemplateState)

        # Double Check: No state shall refer to a Door of the combined states.
        if False:
            for state in self.__elect_db.itervalues():
                for door_id in state.entry.door_db.itervalues():
                    assert door_id.state_index != i 
                    assert door_id.state_index != k 
                    if door_id.state_index != elect.index:
                        assert self.__elect_db.has_key(door_id.state_index), \
                               "%s\n--\n%s\n" % (state.entry.transition_db, door_id)
                        target_state = self.__elect_db[door_id.state_index]
                        assert target_state.entry.transition_db.has_key(door_id), \
                               "%s\n--\n%s\n" % (target_state.entry.transition_db, door_id)
                for door_id in state.entry.transition_db.iterkeys():
                    assert door_id.state_index != i 
                    assert door_id.state_index != k 
                    if door_id.state_index != elect.index:
                        assert self.__elect_db.has_key(door_id.state_index), \
                               "%s\n--\n%s\n" % (state.entry.transition_db, door_id)
                        target_state = self.__elect_db[door_id.state_index]
                        assert target_state.entry.transition_db.has_key(door_id), \
                               "%s\n--\n%s\n" % (target_state.entry.transition_db, door_id)
                for interval, target in state.transition_map:
                    if target.drop_out_f: 
                        continue
                    elif target.door_id is not None:
                        assert door_id.state_index != i 
                        assert door_id.state_index != k 
                        if door_id.state_index != elect.index:
                            assert self.__elect_db.has_key(door_id.state_index), \
                                   "%s\n--\n%s\n" % (state.entry.transition_db, door_id)
                            target_state = self.__elect_db[door_id.state_index]
                            assert target_state.entry.transition_db.has_key(door_id), \
                                   "%s\n--\n%s\n" % (target_state.entry.transition_db, door_id)
                    else:
                        for door_id in target.scheme:
                            assert door_id.state_index != i 
                            assert door_id.state_index != k 
                            if door_id.state_index != elect.index:
                                assert self.__elect_db.has_key(door_id.state_index), \
                                       "[%i] %s\n--\n%s\n" % (state.index, state.entry.transition_db, door_id)
                                target_state = self.__elect_db[door_id.state_index]
                                assert target_state.entry.transition_db.has_key(door_id), \
                                       "%s\n--\n%s\n" % (target_state.entry.transition_db, door_id)

    def __assert_transition_map(self, TheState):
        """A transition map shall never contain the root door of
           a TemplateState, except of its own.
        """
        for interval, target in TheState.transition_map:
            if target.drop_out_f: 
                continue
            elif target.door_id is not None:
                if   target.door_id == E_StateIndices.DROP_OUT:
                    continue
                elif target.door_id.door_index != 0: 
                    continue
                elif target.door_id.state_index != TheState.index: 
                    target_state = self.__all_db[target.door_id.state_index]
                    assert not isinstance(target_state, TemplateState)
            else:
                for door_id in target.scheme:
                    if   door_id == E_StateIndices.DROP_OUT:
                        continue
                    elif door_id.door_index != 0: 
                        continue
                    elif door_id.state_index != TheState.index: 
                        target_state = self.__all_db[door_id.state_index]
                        assert not isinstance(target_state, TemplateState)
