from   quex.engine.misc.tree_walker             import TreeWalker
from   quex.engine.analyzer.examier.recipe_base import Recipe

import types
from   collections import defaultdict
from   itertools   import chain

class LinearStateInfo:
    """.recipe        = Accumulated action Recipe(i) that determines SCR(i) after 
                        state has been entered.

    The '.recipe' is determined from a spring state, or through accumulation of
    linear states. The 'on_drop_out' handler can be determined as soon as 
    '.recipe' is determined.
    """
    __slots__ = ("recipe")

class MouthStateInfo:
    """.recipe   = Recipemulated action Recipe(i) that determines SCR(i) 
                        after state has been entered.
       .entry_db = map: from 'TransitionID' to accumulated action at entry 
                        into mouth state.

    The '.entry_db' is filled each time a walk along a sequence of linear
    states reaches a mouth state. It is complete, as soon as all entries into
    the state are present in the keys of '.entry_db'. Then, an interference
    may derive the '.recipe' which determines the SCR(i) as soon as the state has
    been entered.  
    """
    __slots__ = ("recipe", "entry_db")

class Examiner:
    def __init__(self, SM, RecipeType):
        assert issubclass(RecipeType, Recipe)
        self.sm          = SM
        self.recipe_type = RecipeType

        self.mouth_db    = {}
        self.linear_db   = {}

    def do(self):
        """Associate all states in the state machine with an 'R(i)' and
        determine what actions have to be implemented at what place.
        """
        self.scr_db = self.determine_SCRs()

        # Determine what states are entered only by one state. Those are the 
        # 'linear states'. States which are entered by more than one state are
        # 'mouth states'.
        self.linear_db, \
        self.mouth_db   = self.categorize_states()

        # Determine states from where a walk along linear states can begin.
        springs = self.recipe_type.determine_initial_springs()

        # Resolve as many as possible states in the state machine, i.e. 
        # associate the states with an recipe 'R(i)'.
        unresolved_mouths = self.resolve(springs)

        # Resolve the states which have been identified to be dead-locks. After
        # each resolved dead-lock, resolve depending linear states.
        self.resolve_dead_locks(unresolved_mouths)

        # At this point all states must have determined recipes, according to
        # the theory in 00-README.txt.
        assert self.determined_set == set(self.sm.states.iterkeys())

    def determine_initial_springs():
        """Finds the states in the state machine that comply to the condition
        of a 'spring' as defined in 00-README.txt. It determines the recipe for
        those springs and adds them to the databases.

        RETURNS: list of state indices of initial spring states.
        """
        springs = self.recipe_type.determine_initial_springs()
        for state_index in springs:
            recipe = self.recipe_type.from_spring(self.sm[state_index])
            self.add_recipe(state_index, recipe)

    def determine_SCRs(self):
        """Determines SCR(i), that is it determines the registers which are 
        important for each state. For that the 'terminals' are requested from 
        the recipe type (representing the investigated behavior). 
        
        If a state 'i' requires a register 'x' for its drop-out procedure, then
        the development of 'x' along the states on the path to 'i' must be 
        implemented. In other words, 'x' is part of any SCR(k) where 'k' is a
        predecessor state of 'i'.

        The method to resolve this is 'back-propagation' of needs.
        """
        # terminal_scr_db = defaultdict(set)
        terminal_scr_db = self.recipe_type.get_SCR_terminal_db(self.sm)

        # SCR(i) for all states determined => back-propagation not necessary.
        if len(terminal_scr_db) == len(self.sm.states):
            return terminal_scr_db

        # Determine SCR(i) of states on which determined states depend
        propagated_db = defaultdict(set)
        for si, sov in terminal_scr_db:
            predecessor_set = self.predecessor_db[si]
            propagated_db.update(
                (psi, sov) for psi in predecessor_set
            )

        # Include propagated sovs into already known ones
        scr_db = terminal_scr_db
        for si, sov in propagated_db.iteritems():
            # SCR(i) takes over what is reported in 'propagated_db[i]'
            scr_db[si].update(sov)

        return scr_db

    def categorize_states(self):
        """Seperates the states in state machine into two sets:

        RETURNS: [0] linear states (only ONE entry from another state)
                 [1] mouth states (entries from MORE THAN ONE state)

        The init state is special, in a sense that it is entered from outside
        without explicit mentioning. Therefore, it is only a linear state
        if it has NO entry from another state.
        """
        from_db = self.sm.get_from_db()

        linear_db = {}
        mouth_db  = {}
        def add(StateIndex, Limit):
            """Determine in what list the StateIndex needs to be put based on
            the number of states from which it is entered.
            """
            if len(from_db[StateIndex]) <= Limit: 
                return linear_db[StateIndex] = LinearStateInfo()
            else:                                
                return mouth_db[StateIndex]  = MouthStateInfo()

        add(self.sm.init_state_index, 0)
        for state_index in self.sm.states.iterkeys():
            if state_index == InitStateIndex: continue
            add(state_index, 1)

        return linear_db, mouth_db

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
        new_springs = Springs
        while new_springs:
            # Derive recipes along linear states starting from springs.
            determined_mouths = self._accumulate(springs) 

            # Resolved mouth states -> new springs for '_accumulate()'
            self._interfere(determined_mouths)

            # The determined mouths become the new springs for the linear walk
            new_springs = determined_mouths

        return set(self.mouth_db.iterkeys()).difference(self.determined_set)

    def resolve_dead_locks(self, UnresolvedMouths):
        """After the process of '.resolve()', there might be remaining mouth
        states which cannot be resolve due to mutual dependencies. Those states
        are called 'dead-lock states'. This function resolves these dead-lock
        states and its dependent states.
        """
        group_set = self.dead_lock_groups_find(UnresolvedMouths)

        for group in self.dead_lock_resolution_sequence(group_set):
            # The only entries into the group are those which are determined.
            entry_db = MouthInfo.collect_determined_entries(
                                             self.mouth_db[si] for si in group)

            # Based on those entries an 'inherent recipe' can be determined.
            recipe = self.recipe_type.from_interference_for_dead_lock_group(entry_db)

            # All dead-lock mouth states propagate the same recipe.
            # (While some entries still may remain open. The become determined
            #  upon a call to '_accumulate()'.            
            for si in group:
                self.add_entry(si, recipe)

            # From the determined mouths, linear walk determine subsequent recipes.
            self._accumulate(Springs=group) 

    def dead_lock_resolution_sequence(self, group_set):
        """As has been proven in 00-README.txt, there is always a non-circular
        dependency hierarchy in dead-lock groups. This is a generator that
        provides an iterator through the groups of 'group_set' in a way so
        that can be resolved sequentially. That is, if a group is yielded than
        it can be resolved. Its resolution on the other hand, is required to 
        solve later groups.

        YIELDS: next group that can and must be resolved.
        """
        def group_dependence(Ga, Gb):
            """RETURNS: True  -- if a state in 'Ga' depends on a state in 'Gb'.
                        False -- if not.
            """
            for si in Ga:
                if not self.depend_db[si].isdisjoint(G): return True
            return False

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
        
        depend_db         = {}
        for ga in group_set:
            deps = set(gb for gb in group_set
                          if ga != gb and depends(ga, gb))
            depend_db[ga] = deps
        
        step_n   = 0
        L        = len(group_set)
        while group_set:
            no_dep_group_set = determined(group_set, sorted_list, depend_db)

            group_set.difference_update(no_dep_group_set)
            for group in no_dep_group_set:
                yield group
            
            step_n += 1
            assert step_n <= L  # Assert to detect loop forever.

    def dead_lock_groups_find(self, UnresolvedMouths):
        """Find dead-lock groups. According to 00-README.txt, a dead-lock
        group is a group where every state depends on the other. There, it 
        has been proven, that a state can only belong to one group.

        RETURNS: Sets of states -- each set is a dead-lock group.
        """

        # map: state index --> indices of states on which it depends.
        depend_db = dict( 
            (umsi, set(si for si in self.predecessor_db[umsi]
                          if si in UnresolvedMouths))
            for umsi in UnresolvedMouths
        )

        # A state can only belong to one group, that is as soon as it treated
        # it does not have to be treated again.
        group_set = set()
        done_set  = set()
        for si, depend_si in depend_db.iteritems():
            if si in done_set: continue
            group = set(
                si_b for si_b in depend_si
                     if si in depend_db[si_b]: group.add(si_b)
            )
            group_set.add(group)
            done_set.update(group)

        return group_set

    def add_recipe(self, StateIndex, TheRecipe):
        """Assign a recipe to a state. As soon as this happens, the state is
        considered 'determined' and added to '.determined_set'.
        """
        info = self.linear_db.get(StateIndex)
        if info is not None: info.recipe                      = TheRecipe
        else:                self.mouth_db[StateIndex].recipe = TheRecipe
        self.determined_set.add(StateIndex)

    def get_recipe(self, StateIndex):
        """This function is only supposed to be called for determined states.

        RETURNS: Recipe for given state index.
        """
        info = self.linear_db.get(StateIndex)
        if info is not None: return info.recipe
        else:                return self.mouth_db[StateIndex]

    def _accumulate(self, Springs):
        """Recursively walk along linear states. The termination criteria is 
        that one of three things hold:

            -- The state is a terminal and has no successors.
            -- The state ahead is a mouth state
            -- The state ahead has a determined recipe.

        An accumulated action is determined on each step by

                recipe = self._accumulate(recipe, State)

        """
        walker = LinearStateWalker(self.recipe_type, 
                                   self.sm.states, 
                                   self.determined_set,
                                   self.linear_db, 
                                   self.mouth_db)

        for si in Springs:
            # spring == determined state => 'get_recipe()' MUST work.
            recipe = self.get_recipe(si)
            walker.add_recipe(si, recipe)
            walker.do((si, recipe))

        # self.determined_set == walker.determined_set
        return walker.determined_mouths

    def _interfere(self, DeterminedMouthSet):
        """Perform interference of mouth states. Find for each state index the
        MouthInfo and determine the interfered recipe by '.recipe_type', i.e.
        according to the investigated behavior.

        MouthInfo.recipe:     = recipe of resolved mouth state.
        self.determined_set:  add determined mouth state index
        """
        for si in DeterminedMouthSet:
            recipe = self.recipe_type.from_interference(self.mouth_db[si])
            self.add_recipe(si, recipe)

class LinearStateWalker(TreeWalker):
    """Walks recursively along linear states until it reaches a terminal, until the
    state ahead is a mouth state, or a determined state.

        -- Performs the accumulation according to the given 'RecipeType'. 

        -- Every state, for which a recipe is determined, is added to the 
           'determined_set'. 

        -- Every mouth state for wich all entry recipies are defined, is added
           to the 'determined_mouths' set.

    The 'determined_mouths' will later be determined through 'interference' and
    as then they will be added to 'determined_set'--but not now!
    """
    @typed(RecipeType=types.ClassType)
    def __init__(self, RecipeType, StateDb, DeterminedStateIndexSet, MouthDb):
        self.recipe_type = RecipeType
        self.state_db    = StateDb
        self.mouth_db    = MouthDb

        self.determined_set    = DeterminedStateIndexSet
        self.determined_mouths = set()

        TreeWalker.__init__(self)

    def on_enter(self, Args):
        StateIndex = Args[0]
        PrevRecipe = Args[1]
        # Accumulation: Concatenate recipe of previous state with operation
        #               of current state.
        # => recipe of current state.
        state  = self.state_db[StateIndex]
        recipe = self.recipe_type.from_accumulation(PrevRecipe, 
                                                    state.single_entry)
        examiner.add_recipe(StateIndex, recipe)

        # Termination Criteria:
        # (i)   Terminal: no transitions, do further recursion. 
        #       (Nothing to be done to guarantee that)
        # (ii)  Do not enter a mouth state.        
        # (iii) Target is determined (spring).               
        todo = []
        for target_index, transition_id in state.target_map().iteritems():
            mouth_info = self.mouth_db.get(target_index)
            if mouth_info is not None:
                # (ii) Consider mouth state --> not in 'todo'.
                target   = self.state_db[target_index]
                e_recipe = self.recipe_type.from_accumulation(recipe, 
                                                              target.single_entry)
                mouth_info.entry_db.enter(transition_id, e_recipe)
                if mouth_info.is_determined():
                    self.determined_mouths.append(target_index)
                continue # Do not dive into mouth states!
            elif target.index in self.determined_set:
                # (iii) Target is determined --> not in 'todo'.
                continue
            else:
                todo.append((target_index, recipe))

        if not todo: return None
        else:        return todo

