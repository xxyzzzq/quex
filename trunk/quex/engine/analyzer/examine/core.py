
E_RecipeType = Enum("UNDETERMINED", "VOID", "__DEBUG_E_RecipeType")

DeadLockGroup = namedtuple("DeadLockGroup", 
                           ("state_index_set", "dependency_set"))

class Recipe:
    """Base class for SOV recipes. The general recipe depends on:

        -- The current state.
        -- Constants which can be pre-determined.
        -- Register contents which are developed at run-time.

    See 00-README.txt the according DEFINITION.
    """
    @staticmethod
    def is_spring(TheState):
        """RETURNS: True  -- if TheState complies with the requirements of a 
                             spring state.
                    False -- else.

        In a spring the Recipe(i) must be determined. That is, as soon as this
        state is entered any history becomes unimportant. The setting of the
        SOV(i) can be determined from an Recipe(i).
        """
        assert False

    @staticmethod
    def from_spring(SpringState):
        """RETURNS: An accumulated action that determines the setting of the
                    SOV(i) after the SpringState has been entered.
        """
        assert False

    @staticmethod
    def from_accumulation(Recipe, LinearState):
        """RETURNS: An accumulated action that expresses the concatenation of
                    the given Recipe, with the operation at entry of LinearState.

        The resulting accumulated action determines the setting of SOV(i) after
        the linear state has been entered.
        """
        assert False

    @staticmethod
    def from_interference(RecipeIterable, MouthState):
        """RETURNS: An accumulated action that expresses the interference of 
                    accumulated actions at different entries into a MouthState.
        """
        assert False

    def get_drop_out_CommandList(self):
        """With a given Recipe(i) for a state 'i', the action upon state machine
        exit can be determined.

        RETURNS: A CommandList that corresponds self.
        """
        assert False
    
    def get_entry_CommandList(self, NextRecipe):
        """Consider the NextRecipe with respect to self. Some contents may 
        have to be stored in registers upon entry into this state. 

        RETURNS: A CommandList that allows 'InterferedRecipe' to operate after 
                 the state.

        This is particulary important at mouth states, where 'self' is an 
        entry into the mouth state and 'NextRecipe' is the accumulated action
        after the state has been entered.
        """
        assert False
    
class ResultState:
    __slots__ = ("on_entry_db", "on_drop_out")

    @staticmethod
    def from_LinearState(Recipe, EntryTransitionID, EntryRecipe):
        if EntryRecipe is None:
            ecl = None
        else:
            ecl = EntryRecipe.get_entry_CommandList(Recipe)
        self.on_entry_db[EntryTransitionID] = ecl
        self.on_drop_out = Recipe.get_drop_out_CommandList()

    @staticmethod
    def from_MouthState(RecipeDb, Recipe):
        for transition_id, accu in RecipeDb.iteritems():
            ecl = accu.get_entry_CommandList(Recipe)
            self.on_entry_db[transition_id] = ecl
        self.on_drop_out = Recipe.get_drop_out_CommandList()

class LinearState:
    """.accu        = Recipemulated action Recipe(i) that determines SOV(i) after 
                      state has been entered.

    The '.accu' is determined from a spring state, or through accumulation of
    linear states. The 'on_drop_out' handler can be determined as soon as 
    '.accu' is determined.
    """
    __slots__ = ("accu", "on_drop_out")

class MouthState:
    """.accu        = Recipemulated action Recipe(i) that determines SOV(i) after 
                      state has been entered.
       .accu_db     = map: from 'TransitionID' to accumulated action at entry 
                           into mouth state.

    The '.accu_db' is filled each time a walk along a sequence of linear states
    reaches a mouth state. It is complete, as soon as all entries into the state
    are present in the keys of '.accu_db'. Then, an interference may derive the
    '.accu' which determines the SOV(i) as soon as the state has been entered.
    Only then, the '.on_drop_out' and '.on_entry_db' can be determined.
    """
    __slots__ = ("accu", "accu_db", "on_drop_out", "on_entry_db")

class Strategy:
    def __init__(self, SM, RecipeType):
        self.sm        = SM
        self.accu_type = RecipeType

    def do(self):
        """Associate all states in the state machine with an Recipe(i) and 
        determine what actions have to be implemented at what place.
        """

        # Determine what states are entered only by one state. Those are the 
        # 'linear states'. States which are entered by more than one state are
        # 'mouth states'.
        from_db, dummy          = self.sm.get_from_to_db()
        state_index_set         = self.sm.states.itervalues()
        init_state_index        = self.sm.init_state_index
        linear_list, mouth_list = self.categorize(from_db, 
                                                       init_state_index
                                                       state_index_set)

        # Determine the states from where a walk along a linear sequence of 
        # states makes sense.
        springs = self.filter_springs(linear_list)

        # Resolve as many as possible states in the state machine, i.e. 
        # associate the states with an accumulated action 'Recipe(i)'.
        dead_lock_list  = self.resolve(springs, mouth_list)

        # Resolve the states which have been identified to be dead-locks.
        self.resolve_dead_lock(dead_lock_list)

    @staticmethod
    def categorize(FromDb, InitStateIndex, StateIndexIterable):
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

    def filter_springs(self, CandidateList):
        """RETURNS: list of state indices from CandidateList where the according
                    state can be the begin of a walk along a sequence of linear
                    states.
        """
        return [
            state_index
            for state_index in CandidateList
            if self.accu_type.is_spring(state_index)
        ]

    def resolve(self, BeginList, MouthList):
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

    def resolve_dead_lock(self, DeadLockList):
        """During the process of '.resolve()', there might be remaining mouth
        states which cannot be resolve due to mutual dependencies. Those states
        are called 'dead-lock states'. This function resolves these dead-lock
        states and its dependent linear states.
        """
        dependency_db       = self.get_dependency_db(DeadLockList)
        dead_lock_group_set = self.get_dead_lock_groups(dependency_db)
        resolution_sequence = _dead_lock_resolution_sequence(group_set)

        for group in resolution_sequence:
            _dead_lock_resolve(group)
            resolved, unresolved = _accumulate(Springs=group)

    def dead_lock_groups_find(DeadLockList):
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

    def get_dead_lock_groups(self, DependencyDb):
        """Determine groups of dead-lock mouth states where all states
        that belong to it are mutually dependent.

        RETURNS: set of groups of dead-lock states.
        """
        # A 'dead-lock-group' is a group where for all states 'i' in the group
        # the depend_db[i] == the group itself.
        dead_lock_group_set = set(DependencyDb.itervalues())

        for group in dead_lock_group_set:
            accu = self.accu_type.from_interference(flatten(x.accu_in_list for x in group))
            for mouth in group:
                assign(mouth, accu)

        return dead_lock_group_set

    def _interfere(self, MouthStateList):
        """Perform interference of mouth states.
        """
        resolved   = []
        unresolved = []
        for state in MouthStateList:
            accu_out = self.accu_type.from_interference(
                accu for i, accu in state.accu_db.iteritems()
            )
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
            accu = self.accu_type.from_accumulation(prev_accu, state.action)

            # Termination Criteria:
            # (i)   Terminal: no transitions, do further recursion. 
            #       (Nothing to be done to guarantee that)
            # (ii)  Do not enter a mouth state.
            # (iii) Consider Strategy specific criteria.
            todo = [
                target
                for target in state.transitions()
                if entrance_ok(transition_id, target)
            ]

            if not todo: return None
            else:        return todo

        def entrance_ok(transition_id, target):
            """RETURNS: False -- if the state 'Target' should not be entered.
                        True  -- if it should
            """
            if target in mouth_state_list: 
                target.accu_db[transition_id] = accu 
                return False
            elif self.accu_type.is_spring(TargetStateIndex): 
                return False
            else:                                            
                return True

   return linear_state_list, mouth_state_list
