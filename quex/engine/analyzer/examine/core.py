
E_AccuType = Enum("UNDETERMINED", "VOID", "__DEBUG_E_AccuType")

DeadLockGroup = namedtuple("DeadLockGroup", 
                           ("state_index_set", "dependency_set"))

class Strategy:
    """Base class for analysis strategies.
    """
    def __init__(self, SM):
        self.sm = SM

    def base_do(self):
        """Associate all states in the state machine with an Accu(i) and 
        determine what actions have to be implemented at what place.
        """

        # Determine what states are entered only by one state. Those are the 
        # 'linear states'. States which are entered by more than one state are
        # 'mouth states'.
        from_db, dummy   = self.sm.get_from_to_db()
        state_index_set  = self.sm.states.itervalues()
        init_state_index = self.sm.init_state_index
        linear_list, mouth_list = Strategy.base_categorize(from_db, 
                                                           init_state_index
                                                           state_index_set)

        # Determine the states from where a walk along a linear sequence of 
        # states makes sense.
        springs = self.base_filter_springs(linear_list)

        # Resolve as many as possible states in the state machine, i.e. 
        # associate the states with an accumulated action 'Accu(i)'.
        dead_lock_list  = self.base_resolve(springs, mouth_list)

        # Resolve the states which have been identified to be dead-locks.
        self.base_resolve_dead_lock(dead_lock_list)

    @staticmethod
    def base_categorize(FromDb, InitStateIndex, StateIndexIterable):
        """Seperates the states in state machine into two sets:

        RETURNS: [0] linear states (only ONE entry from another state)
                 [1] mouth states (entries from MORE THAN ONE state)

        The init state is special, in a sense that it is entered from outside
        without explicit mentioning. Therefore, it is only a linear state
        if it has NO entry from another state.
        """
        linear_list = []
        mouth_list  = []

        def container(StateIndex, Limit=1):
            """Determine in what list the StateIndex needs to be put based on
            the number of states from which it is entered.
            """
            if len(from_db[StateIndex]) <= Limit: return linear_list
            else:                                 return mouth_list

        container(InitStateIndex, 0).append(InitStateIndex)
        for state_index in StateIndexIterable:
            if state_index == init_state_index: continue
            container(state_index).append(state_index)

        return linear_list, mouth_list

    def base_filter_springs(self, CandidateList):
        """RETURNS: list of state indices from CandidateList where the according
                    state can be the begin of a walk along a sequence of linear
                    states.
        """
        return [
            state_index
            for state_index in CandidateList
            if self.has_determined_accu(state_index)
        ]

    def base_entrance_ok(self, TargetStateIndex):
        """RETURNS: False -- if the state 'Target' should not be entered.
                    True  -- if it should
        """
        if   TargetStateIndex in self.mouth_set:         return False
        elif self.has_determined_accu(TargetStateIndex): return False
        else:                                            return True

    def base_resolve(self, BeginList, MouthList):
        """.--->  (1) Walk along linear states from the states in the set of 
           |          begin states. Derive accumulated actions along the walk.
           |      
           |      (2) Resolve mouth states, if possible according to their entries. 
           |          Interfere the accumulated actions at a mouth state. Once the 
           |          outgoing accumulated action can be determined the mouth state
           |          is resolved.
           |      
           |      (3) Consider the resolved mouth states are new walk-begin states.
           |
           '- no -(*) of walk-begin states is empty?

        The remaining set of unresolved mouth states is mutually dependent and
        requires a 'dead lock treatment'.

        RETURNS: Set of dead-lock mouth states.
        """
        springs = BeginList
        while springs:
            unresolved_mouths          = self._accumulate(springs, MouthList)
            # Resolved mouth states -> new springs for '_accumulate()'
            springs, unresolved_mouths = self._interfere(unresolved_mouths)

        return unresolved_mouths

    def base_resolve_dead_lock(self, DeadLockList):
        """During the process of '.resolve()', there might be remaining mouth
        states which cannot be resolve due to mutual dependencies. Those states
        are called 'dead-lock states'. This function resolves these dead-lock
        states and its dependent linear states.
        """
        dependency_db       = self.base_get_dependency_db(DeadLockList)
        dead_lock_group_set = self.base_get_dead_lock_groups(dependency_db)
        resolution_sequence = _dead_lock_resolution_sequence(group_set)

        for group in resolution_sequence:
            _dead_lock_resolve(group)
            resolved, unresolved = _accumulate(Springs=group)

    def base_dead_lock_groups_find(DeadLockList):
        depend_db = {} # map: state 'i' --> 'state_set' that depend on 'i'

        # (*) Direct dependencies.
        #
        # Detect dependencies originating from connections by linear state
        # sequences.
        for begin in DeadLockList:
            reached_mouths = self.__walk_linear(begin)
            # Any mouth state that has been reached starting from 'begin'
            # depends on the output of 'begin'.
            direct_depend_db.update(
                (mouth, begin) for reached in reached_mouths
            )

         # (*) Include indirect dependencies.
         def iterable(DependDb):
             """YIELDS: set of states on which a state 'x' depends.
                        set of states on which another state depends which depends on 'x'.
             """
             for state, dependends in DependDb.iteritems():
                 for other_dependends in DependDb.itervalues():
                     if state not in other_dependends: continue
                     yield dependends, other_dependends

         change_f = True
         while change_f:
             for dependends, other_dependends in iterable(depend_db):
                 size_before = len(other_dependends)
                 other_dependends.update(dependends)
                 if len(other_dependends) != size_before: change_f = True

         return set(depend_db.itervalues())

    def base_get_dead_lock_groups(self, DependencyDb):
        """Determine groups of dead-lock mouth states where all states
        that belong to it are mutually dependent.

        RETURNS: set of groups of dead-lock states.
        """
        # A 'dead-lock-group' is a group where for all states 'i' in the group
        # the depend_db[i] == the group itself.
        dead_lock_group_set = set(DependencyDb.itervalues())

        for group in dead_lock_group_set:
            accu = Strategy.intefere(flatten(x.accu_in_list for x in group))
            for mouth in group:
                assign(mouth, accu)

        return dead_lock_group_set

    def get_walk_begin_state_list(self):
        """RETURNS: set of indices of states which are suited to be the begin
                    of a walk along a linear sequence of states.
        """
        assert False

    def accumulate(self, PrevAccu, Accu)
        """RETURNS: An accumulated action where an existing accu is mounted
                    on top of a later one.
        """
        assert False

    def interfere(self, AccuList):
        """RETURNS: None                    -- if there are undetermined entries.
                    AccumulatedAction_VOID  -- if the outgoing Accu is 'void'
                    AccumulatedAction       -- the accu that results from interference.

        If None is returned, this means that there can be outgoing accu be determined
        because entries are missing. If 'AccumulatedAction_VOID' is returned that 
        the lack of uniformity of existing entries allows to tell that absolutely
        not common accumulator pattern can be derived. 

        Only in case that a normal 'AccumulatedAction' object is returned, it can 
        be assumed that all entries have been considered and that a common pattern
        could be derived.
        """
        assert False

    def _interfere(self, MouthStateList):
        """Perform interference of mouth states.
        """
        resolved   = []
        unresolved = []
        for state in MouthStateList:
            accu_out = self.interfere(state.accu_in_list)
            if accu_out is None:
                unresolved.append(state)
            else:
                state.accu_out = accu_out
                resolved.append(state)
        return resolved, unresolved

    def _accumulate(Springs):
        """Recursively walk along sequences of linear states. The termination
        criteria is that one of three things hold:

            -- The state is a terminal and has no successors.
            -- The state ahead is a mouth state
            -- self.entrance_ok(SM, StateIndex, TransitionID)

        An accumulated action is determined on each step by

                accu = self.accumulate(accu, State)

        """

        def on_enter(prev_accu):
            accu = self.accumulate(prev_accu, state.action)

            # Termination Criteria:
            # (i)   Terminal: no transitions, do further recursion. 
            #       (Nothing to be done to guarantee that)
            # (ii)  Do not enter a mouth state.
            # (iii) Consider Strategy specific criteria.
            def entrance_ok(target):
                if mouth in mouth_state_list: 
                    mouth.accu_in_list.append((state.index, accu))
                    return False
                return self.entrance_ok(state, target)

            todo = [
                target
                for target in state.transitions()
                if entrance_ok(target)
            ]

            if not todo: return None
            else:        return todo

   return linear_state_list, mouth_state_list
