
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
    def get_SOV_operation(TheState):
        """Extracts from a given state machine state the operation on the SOV, 
        i.e. the set of variables that describe the behavior (see 00-README.txt).

        RETURNS: A description of the operations on the SOV upon entry into 
                 'TheState'.
        """
        assert False

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
    
class LinearState:
    """.recipe        = Recipemulated action Recipe(i) that determines SOV(i) after 
                        state has been entered.

    The '.recipe' is determined from a spring state, or through accumulation of
    linear states. The 'on_drop_out' handler can be determined as soon as 
    '.recipe' is determined.
    """
    __slots__ = ("recipe")

class MouthState:
    """.recipe   = Recipemulated action Recipe(i) that determines SOV(i) 
                        after state has been entered.
       .entry_db = map: from 'TransitionID' to accumulated action at entry 
                        into mouth state.

    The '.entry_db' is filled each time a walk along a sequence of linear
    states reaches a mouth state. It is complete, as soon as all entries into
    the state are present in the keys of '.entry_db'. Then, an interference
    may derive the '.recipe' which determines the SOV(i) as soon as the state has
    been entered.  
    """
    __slots__ = ("recipe", "entry_db")

class Strategy:
    def __init__(self, SM, RecipeType):
        self.sm          = SM
        self.recipe_type = RecipeType

        self.mouth_state_db  = {}
        self.linear_state_db = {}

    def do(self):
        """Associate all states in the state machine with an 'R(i)' and 
        determine what actions have to be implemented at what place.
        """

        # Determine what states are entered only by one state. Those are the 
        # 'linear states'. States which are entered by more than one state are
        # 'mouth states'.
        linears, mouths = Strategy.categorize_states()

        # Determine states from where a walk along linear states can begin.
        springs = self.determine_springs()
        self.determined_state_index_set = set(s.state_index for state in springs)

        # Resolve as many as possible states in the state machine, i.e. 
        # associate the states with an recipe 'R(i)'.
        dead_lock_list = self.resolve(springs, mouth_list)

        # Resolve the states which have been identified to be dead-locks. After
        # each resolved dead-lock, resolve depending linear states.
        self.resolve_dead_lock(dead_lock_list)

        # At this point all states must have determined recipes, according to
        # the theory in 00-README.txt.
        assert self.determined_state_index_set == set(self.sm.states.iterkeys())

    def categorize_states(self):
        """Seperates the states in state machine into two sets:

        RETURNS: [0] linear states (only ONE entry from another state)
                 [1] mouth states (entries from MORE THAN ONE state)

        The init state is special, in a sense that it is entered from outside
        without explicit mentioning. Therefore, it is only a linear state
        if it has NO entry from another state.
        """
        from_db = self.sm.get_from_db()

        def add(StateIndex, Limit):
            """Determine in what list the StateIndex needs to be put based on
            the number of states from which it is entered.
            """
            if len(from_db[StateIndex]) <= Limit: 
                return self.linear_db[StateIndex] = LinearState()
            else:                                
                return self.mouth_db[StateIndex]  = MouthState()

        add(self.sm.init_state_index, 0)
        for state_index in self.sm.states.iterkeys():
            if state_index == InitStateIndex: continue
            add(state_index, 1)

        return [self.sm.states[i] for i in self.linear_db], \
               [self.sm.states[i] for i in self.mouth_db]

    def determine_springs(self):
        """Iterates through all states of a given state machine and determines
        the states from where a walk along linear states may begin, so called 
        'springs' (see 00-README.txt). For the springs recipes are derived and
        they are registered in '.determined_state_index_set'.

        MODIFIES: .determined_state_index_set
                  .mouth_db
                  .linear_db

        RETURNS: list of state indices from CandidateList where the according
                 state can be the begin of a walk along a sequence of linear
                 states.
        """
        spring_list = [
            state
            for state in self.sm.states.itervalues()
            if self.recipe_type.is_spring(state)
        ]
        for state in spring_list:
            self.determined_state_index_set.add(state.index)
            recipe = self.recipe_type.from_spring(state)
            if state.state_index in self.mouth_db:
                self.mouth_db[state.state_index].recipe = recipe 
            else:
                self.linear_db[state.state_index].recipe = recipe
        return spring_list

    def resolve(self, Springs, MouthList):
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

        RETURNS: Set of mouth states that could still not be resolved.
                 => They become subject to 'dead-lock treatment'.
        """
        new_springs = Springs
        while new_springs:
            unresolved_mouths              = self._accumulate(springs) 
            # Resolved mouth states -> new springs for '_accumulate()'
            new_springs, unresolved_mouths = self._interfere(unresolved_mouths)

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
            recipe = self.recipe_type.from_interference(flatten(x.accu_in_list for x in group))
            for mouth in group:
                assign(mouth, recipe)

        return dead_lock_group_set

    def _interfere(self, MouthStateList):
        """Perform interference of mouth states.
        """
        resolved   = []
        unresolved = []
        for state in MouthStateList:
            accu_out = self.recipe_type.from_interference(
                recipe for i, recipe in state.entry_db.iteritems()
            )
            if accu_out is None:
                unresolved.append(state)
            else:
                state.accu_out = accu_out
                resolved.append(state)
        return resolved, unresolved

    def _accumulate(Springs):
        """Recursively walk along linear states. The termination criteria is 
        that one of three things hold:

            -- The state is a terminal and has no successors.
            -- The state ahead is a mouth state
            -- The state ahead has a determined recipe.

        An accumulated action is determined on each step by

                recipe = self._accumulate(recipe, State)

        """

        def entrance_ok(transition_id, target):
            """RETURNS: False -- if the state 'Target' should not be entered.
                        True  -- if it should
            """
            if target_index in self.determined_state_index_set:
                return False
            elif target_index in self.mouth_db: 
                self.mouth_db.entry_db.enter(transition_id, recipe)
                return False
            return True

        def on_enter(prev_state, prev_recipe):
            recipe = self.recipe_type.from_accumulation(
                             prev_recipe, 
                             self.recipe_type.get_SOV_operation(state))

            # Termination Criteria:
            # (i)   Terminal: no transitions, do further recursion. 
            #       (Nothing to be done to guarantee that)
            # (ii)  Do not enter a mouth state.          --> entrance_ok()
            # (iii) Consider Strategy specific criteria. --> entrance_ok()
            todo = [
                target
                for target, transition_id in state.transitions()
                if entrance_ok(transition_id, target)
            ]

            if not todo: return None
            else:        return todo

   return linear_state_list, mouth_state_list
