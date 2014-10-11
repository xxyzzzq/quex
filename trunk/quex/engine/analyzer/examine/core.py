E_AccuType = Enum("UNDETERMINED", "VOID", "__DEBUG_E_AccuType")

class Strategy:
    """Base class for analysis strategies.
    """
    def get_walk_begin_state_list(self, LinearStateList):
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

    def entrance_ok(self, State, Target):
        """RETURNS: False -- if the state 'Target' should not be entered.
                    True  -- if it should
        """
        assert False

    def step(self, BeginList, MouthList):
        """.--->  (1) Walk along linear states from the states in the set of begin states.
           |          Derive accumulated actions along the walk.
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
        begin_list = BeginList
        while begin_list:
            unresolved_mouths             = self.__walk_linears(begin_list, MouthList)
            # Resolved mouth states -> new begin states for 'walk_linears()'
            begin_list, unresolved_mouths = self.__resolve_mouths(unresolved_mouths)

        return unresolved_mouths

    def dead_lock_treatment(self, DeadLockList):
        direct_depend_db = {} # map: state 'i' --> 'state_set'
        #                       state 'i' directly depends on outcome of states 
        #                       in 'state_set'
        for begin in DeadLockList:
            reached_mouths = self.__walk_linear(begin)
            # Any mouth state that has been reach from 'begin' depends on the
            # output of 'begin'.
            direct_depend_db.update(
                (mouth, begin) for reached in reached_mouths
            )

         depend_db = direct_depend_db # map: state'i' --> 'state_set'
         #                              state 'i' depends on all in 'state_set'
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
             for dependends, other_dependends in iterable():
                 size_before = len(other_dependends)
                 other_dependends.update(dependends)
                 if len(other_dependends) != size_before: change_f = True

         # Now depend_db:
         #
         #    state 'i' --> all states that depend on output of state 'i'.
         #
         # A 'dead-lock-group' is a group where for all states 'i' in the group
         # the depend_db[i] == the group itself.
         dead_lock_group_set = set()
         for group in depend_db.itervalues():
             for i in group:
                 if depend_db[i] != group: break
             else:
                 dead_lock_group_set.add(group)

         for group in dead_lock_group_set:
             accu = Strategy.intefere(flatten(x.accu_in_list for x in group))
             for mouth in group:
                 assign(mouth, accu)

         return flatten(dead_lock_group_set)



        




    def __resolve_mouths(self, MouthStateList):
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

    def __walk_linears(BeginStateList):
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

def do(SM, Strategy):

    linear_list, mouth_list  = categorize(SM)

    walk_begin_list = Strategy.get_walk_begin_state_list(SM, linear_list)

    while walk_begin_list:
        dead_locks           = Strategy.step(walk_begin_list, mouth_list)
        resolved, dead_locks = Strategy.dead_lock_treatment(dead_locks)
        walk_begin_list      = resolved

    if dead_locks:
        Strategy.solve_total_dead_locks(dead_locks)
        walk(dead_locks)

    return

def categorize(SM):
    """Seperates the states in state machine into two sets:

    RETURNS: [0] linear states (only one entry from another state)
             [1] mouth states (entries from more than one state)
    """
    linear_state_list = []
    mouth_state_list  = []
    from_db, dummy = SM.get_from_to_db()
    for state_index, state in SM.states.iteritems():
        if len(from_db[state_index]) <= 1: 
            linear_state_list.append(state_index)
        else:
            mouth_state_list.append(state_index)

   return linear_state_list, mouth_state_list
