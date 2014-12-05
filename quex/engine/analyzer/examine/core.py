from   quex.engine.analyzer.examine.recipe_base  import Recipe
from   quex.engine.analyzer.examine.state_info   import LinearStateInfo, \
                                                        MouthStateInfo
from   quex.engine.misc.tree_walker              import TreeWalker
from   quex.engine.misc.tools                    import all_true, typed

import types
from   itertools import chain

class Examiner:
    def __init__(self, SM, RecipeType):
        assert issubclass(RecipeType, Recipe)
        self.sm          = SM
        self.from_db     = self.sm.get_from_db()
        self.recipe_type = RecipeType

        self.linear_db   = {}  # map: state index --> LinearStateInfo
        self.mouth_db    = {}  # map: state index --> MouthStateInfo

    def do(self):
        """Associate all states in the state machine with an 'R(i)' and
        determine what actions have to be implemented at what place.
        """
        # Categorize states:
        #    .linear_db: 'linear states' being entered only from one state.
        #    .mouth_db:  'mouth states' being entered from multiple states.
        for state_index in self.sm.states.iterkeys():
            self.categorize(state_index)

        # Categorize => StateInfo-s are in place.
        # Now, determine SCRs per state.
        for si, scr in self.recipe_type.get_scr_by_state_index(self.sm):
            self.get_state_info(si).scr = scr

        # Determine states from where a walk along linear states can begin.
        springs = self.determine_initial_springs()

        # Resolve as many as possible states in the state machine, i.e. 
        # associate the states with an recipe 'R(i)'.
        unresolved_mouths = self.resolve(springs)

        # Resolve the states which have been identified to be dead-locks. After
        # each resolved dead-lock, resolve depending linear states.
        for group in self.dead_lock_resolution_sequence(unresolved_mouths):
            # group = set of state indices which belong to the group
            self.resolve_dead_lock_group(group)

        # At this point all states must have determined recipes, according to
        # the theory in 00-README.txt.
        assert all_true(chain(self.linear_db.itervalues(), self.mouth_db.itervalues()), 
                        lambda x: x.is_determined()) 

    def categorize(self, StateIndex):
        """Separates the states of state machine into two categories 
        represented by '.linear_db' and '.mouth_db':

              linear states: only ONE entry from another state.
              mouth states:  entries from MORE THAN ONE state.

        The init state is special, in a sense that it is entered from outside
        without explicit mentioning. Therefore, it is only a linear state
        if it has NO entry from another state.

        All states in '.linear_db' and '.mouth_db' have a 'None' recipe. That
        indicates that they are NOT determined, yet.
        """

        # The init state has an unmentioned entry from 'START'. Thus, if it 
        # is entered by an explicit entry, then it already has two entries 
        # and therefore must become a 'mouth' state.
        if StateIndex == self.sm.init_state_index: limit = 0
        else:                                      limit = 1
            
        from_state_set = self.from_db[StateIndex]
        if len(from_state_set) <= limit: 
            self.linear_db[StateIndex] = LinearStateInfo()
        else:                                
            self.mouth_db[StateIndex]  = MouthStateInfo(from_state_set)

    def determine_initial_springs(self):
        """Finds the states in the state machine that comply to the condition
        of a 'spring' as defined in 00-README.txt. It determines the recipe for
        those springs and adds them to the databases.

        RETURNS: list of state indices of initial spring states.
        """
        springs = self.recipe_type.determine_initial_springs(self.sm)
        for state_index in springs:
            recipe = self.recipe_type.from_spring(self.sm.states[state_index])
            self.set_recipe(state_index, recipe)

    def resolve(self, Springs):
        """.--->  (1) Walk along linear states from the states in the set of 
           |          Springs. Derive recipes along the walk.
           |      
           |      (2) Resolve mouth states, if possible according to their entries. 
           |          Interfere the recipes at a mouth state. Result: recipe of 
           |          the mouth state.
           |      
           |      (3) Consider the resolved mouth states are new springs.
           |
           '- no -(+) springs = empty?
                   |
                   |  yes  
                   |
                  (4) done, for now.

        RETURNS: Set of mouth states that could still not be resolved.
                 => They become subject to 'dead-lock treatment'.
        """
        springs = Springs
        while springs:
            # Derive recipes along linear states starting from springs.
            mouths_ready_set = self._accumulate(springs) 

            # Mouth states where all entry recipes are set
            # => Apply 'interference' to determine their recipe.
            self._interfere(mouths_ready_set)

            # The determined mouths become the new springs for the linear walk
            springs = mouths_ready_set

        # Return the set of still undetermined mouth states.
        return set(si for si, mouth in self.mouth_db.iteritems()
                      if not mouth.is_determined())

    def resolve_dead_lock_group(self, Group):
        """After the process of '.resolve()', there might be remaining mouth
        states which cannot be resolve due to mutual dependencies. Those states
        are called 'dead-lock states'. This function resolves these dead-lock
        states and its dependent states.
        """
        mouth_list = [ self.mouth_db[si] for si in Group ]
            
        # Based on those entries an 'inherent recipe' can be determined.
        self.recipe_type.interfere_in_dead_lock_group(mouth_list)

        # All dead-lock mouth states propagate the same recipe.
        # (While some entry recipes still may remain open)
        return self._accumulate(Group)

    def dead_lock_resolution_sequence(self, UnresolvedMouths):
        """As has been proven in 00-README.txt, there is always a non-circular
        dependency hierarchy in dead-lock groups. This is a generator that
        provides an iterator through the groups of 'group_set' in a way so
        that it can be resolved sequentially. That is, if a group is yielded 
        than it can be resolved. Its resolution on the other hand, is required 
        to solve later groups.

        YIELDS: next group that can and must be resolved.
        """
        def determined(GroupSet, PresentGroupSet, DependDb):
            """Determines which groups from the GroupSet can be determined
            according to the 'PresentGroupSet' and the 'DependDb'. 

            NOTE: At the first call 'PresentGroupSet' is empty. Thus, only
            those groups are returned which do not depend on any other.
            """
            result = set(group for group in GroupSet
                               if DependDb[group].issubset(PresentGroupSet))
            assert result
            return result

        # map: group --> groups on which group depends
        group_depend_db  = self.dead_lock_groups_find(UnresolvedMouths)
        
        determined_set = set()
        while group_depend_db:
            # Find those groups that only depends on groups which have been
            # determined, so far.
            no_dependency_set = determined(group_depend_db, determined_set)
            # According to 00-README.txt, there must be always at least one
            # group that does not depend on others.
            assert no_dependency_set

            for group in no_dependency_set:
                yield group
                del group_depend_db[group]
            # The theory forbids an indefinite loop. An erroneous behavior is
            # caught: (1) through the assert that requires that the 
            #             'no_dependency_set' cannot be empty. 
            #         (2) through the deletion of each group from 
            #             'group_depend_db'. 
            # Thus, the size of 'group_depend_db' decreases always, or an error
            # is thrown that a non-existing group is tried to be deleted.

    def dead_lock_groups_find(self, UnresolvedMouths):
        """Find dead-lock groups. According to 00-README.txt, a dead-lock
        group is a group where every state depends on the other. It has been 
        proven in 00-README.txt, that a state can only belong to one group.

        RETURNS: Dictionary
        
           map: group --> groups on which it depends
           
        """
        def has_dependence(state_depend_db, Ga, Gb):
            """RETURNS: True  -- if a state in 'Ga' depends on a state in 'Gb'.
                        False -- if not.
            """
            for si in Ga:
                if not state_depend_db[si].isdisjoint(Gb): return True
            return False

        predecessor_db = self.sm.get_predecessor_db()
        
        # map: state index --> indices of states on which it depends.
        state_depend_db = dict( 
            (umsi, set(si for si in predecessor_db[umsi]
                          if si in UnresolvedMouths))
            for umsi in UnresolvedMouths
        )
        
        # A state can only belong to one group, that is as soon as it treated
        # it does not have to be treated again.
        group_set = set()
        done_set  = set()
        for si_a, depend_si_a_list in state_depend_db.iteritems():
            if si_a in done_set: continue
            group = set(
                si_b for si_b in depend_si_a_list
                     if si in state_depend_db[si_b]
            )
            group_set.add(group)
            done_set.update(group)

        depend_db = {} # map: group --> groups on which it depends
        for ga in group_set:
            deps = set(gb for gb in group_set
                          if ga != gb and has_dependence(state_depend_db, ga, gb))
            depend_db[ga] = deps

        return depend_db

    def get_state_info(self, StateIndex):
        """RETURNS: LinearStateInfo/MouthStateInfo for a given state index.
        """
        info = self.linear_db.get(StateIndex)
        if info is not None: return info
        else:                return self.mouth_db[StateIndex]

    def set_recipe(self, StateIndex, TheRecipe):
        """Assign a recipe to a state. As soon as this happens, the state is
        considered 'determined'.
        """
        assert self.get_stateinfo(StateIndex).recipe is None
        self.get_state_info(StateIndex).recipe = TheRecipe
        # Since the .recipe is no longer 'None', the state is 'determined'.

    def get_recipe(self, StateIndex):
        """This function is only supposed to be called for determined states.

        ASSUMPTION: 'get_recipe()' is ONLY called for spring states. Thus,
        the state must be determined and the recipe MUST be registered either
        in '.linear_db' or '.mouth_db'.

        RETURNS: Recipe for given state index.
        """
        return self.get_state_info(StateIndex).recipe

    def _accumulate(self, Springs):
        """Recursively walk along linear states. The termination criteria is 
        that one of three things hold:

            -- The state is a terminal and has no successors.
            -- The state ahead is a mouth state
            -- The state ahead has a determined recipe.

        An accumulated action is determined on each step by

                recipe = self._accumulate(recipe, State)

        """
        walker = LinearStateWalker(self)

        for si in Springs:
            # spring == determined state => 'get_recipe()' MUST work.
            walker.do((si, self.get_recipe(si)))

        return set(si for si in walker.mouths_touched_set
                      if self.mouth_db[si].is_ready_for_interferences())

    def _interfere(self, DeterminedMouthSet):
        """Perform interference of mouth states. Find for each state index the
        MouthInfo and determine the interfered recipe by '.recipe_type', i.e.
        according to the investigated behavior.

        MouthInfo.recipe:     = recipe of resolved mouth state.
        """
        for si in DeterminedMouthSet:
            # Interference: 
            # --> entry_db: operations that MUST be done upon entry from a state.
            # --> recipe:   for 'drop_out' and further accumulation.
            self.recipe_type.interfere(self.mouth_db[si])

class LinearStateWalker(TreeWalker):
    """Walks recursively along linear states until it reaches a terminal, until the
    state ahead is a mouth state, or a determined state.

        -- Performs the accumulation according to the given 'RecipeType'. 

        -- Every mouth state for which all entry recipes are defined, is added
           to the 'determined_mouths' set.

    The 'determined_mouths' will later determine their .recipe through 'interference'.
    """
    @typed(TheExaminer=Examiner)
    def __init__(self, TheExaminer):
        self.examiner           = TheExaminer
        self.mouths_touched_set = set()
        TreeWalker.__init__(self)

    def on_enter(self, Args):
        """Consider transitions of current state with determined recipe.
        """
        CurrState, CurrRecipe = Args

        # Termination Criteria:
        # (1) State  = Terminal: no transitions, do further recursion. 
        #                        (Nothing needs to be done to guarantee that)
        # (2) Target is determined  => No entry!
        # (3) Target is Mouth State => No entry!
        todo = []
        for target_index in CurrState.target_map().iterable_target_state_indices():
            target_info = self.examiner.get_state_info(target_index)
            if target_info.is_determined():    
                continue # (2) terminal 
            elif target_info.mouth_f():        
                target_info.entry_recipe_db[target_index] = CurrRecipe
                self.mouths_touched_set.add(target_index)
                continue # (3) terminal 
            else:
                # Linear state ahead => accumulate
                target = self.examiner.sm.states[target_index]
                self.examiner.recipe_type.accumulate(target_info, CurrRecipe, 
                                                     target.single_entry)
                todo.append((target, target_info.recipe))

        if not todo: return None
        else:        return todo


