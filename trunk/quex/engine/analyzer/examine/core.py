from   quex.engine.state_machine.core            import StateMachine
from   quex.engine.analyzer.examine.recipe_base  import Recipe
from   quex.engine.analyzer.examine.state_info   import LinearStateInfo, \
                                                        MouthStateInfo
from   quex.engine.misc.tree_walker              import TreeWalker
from   quex.engine.misc.tools                    import all_true, typed

from   itertools import chain

@typed(SM=StateMachine)
def do(SM, RecipeType):
    """Analyzes a given single-entry state machine and provides information
    about its linear and its mouth states (definition see 00-README.txt).
    The process is controlled by the 'RecipeType'. The type tells about the
    concerned registers and how core elements of the algorithm are performed.
    The RecipeType must be derived from 'recipe_base.Recipe' which ensures
    that all requirement functions are implemented.
    
    By means of RecipeType different kinds of operations may be considered,
    as they are, for example: acceptance behavior, line and column number 
    counting, check-sum computation.
    
    RETURNS: [0] linear_db: state index --> LinearStateInfo
             [1] mouth_db:  state index --> MouthStateInfo
             
    A LinearStateInfo and MouthInfoState provide both the '.recipe', which 
    allows to construct the drop-out behavior of a state. Additionally, a 
    MouthStateInfo the provides the member '.entry_db'. It tells what 
    operations need to be performed upon entry dependent on the 'from-state'.
    """
    assert issubclass(RecipeType, Recipe)
        
    examiner = Examiner(SM, RecipeType)

    # Categorize states:
    #    .linear_db: 'linear states' being entered only from one state.
    #    .mouth_db:  'mouth states' being entered from multiple states.
    examiner.categorize()

    # Categorize => StateInfo-s are in place.
    examiner.determine_scr_by_state()
    
    # Determine states from where a walk along linear states can begin.
    springs = examiner.setup_initial_springs()

    if springs:
        # Resolve as many as possible states in the state machine, i.e. 
        # associate the states with an recipe 'R(i)'. Possibly, there are mouth
        # states with undetermined recipes: dead-lock states.
        unresolved_mouths = examiner.resolve(springs)
    else:
        unresolved_mouths = set(examiner.mouth_db.iterkeys())

    # Solve dead-locks caused by mutual dependencies: 'run-time' interference.
    examiner.resolve_dead_locks(unresolved_mouths)
        
    # At this point all states must have determined recipes, according to
    # the theory in "00-README.txt".
    assert all_true(chain(examiner.linear_db.itervalues(), 
                          examiner.mouth_db.itervalues()), 
                    lambda x: x.is_determined()) 
    
    return examiner.linear_db, examiner.mouth_db

class Examiner:
    """Maintainer of data and provider of operations for the linear state and
    mouth state analysis. Its purpose is to support the sequential process 
    implemented in the global '.do()' function.
    """
    def __init__(self, SM, RecipeType):
        self._sm            = SM
        self.recipe_type    = RecipeType
        self.predecessor_db = SM.get_predecessor_db()

        self.linear_db   = {}  # map: state index --> LinearStateInfo
        self.mouth_db    = {}  # map: state index --> MouthStateInfo

    def categorize(self):
        """Separates the states of state machine into two categories:

           linear states: only ONE entry from another state (-> .linear_db).
           mouth states:  entries from MORE THAN ONE state (-> .mouth_db).

        The init state is special, in a sense that it is entered from outside
        without explicit mentioning. Therefore, it is only a linear state
        if it has NO entry from another state.

        All states in '.linear_db' and '.mouth_db' have a 'None' recipe. That
        indicates that they are NOT determined, yet.
        
        PREPARES: '.linear_db' and '.mouth_db'.
        """
        from_db = self._sm.get_from_db()

        for si in self._sm.states.iterkeys():
            # The init state has an unmentioned entry from 'START'. Thus, if it 
            # is entered by an explicit entry, then it already has two entries 
            # and therefore must become a 'mouth' state.
            if si == self._sm.init_state_index: limit = 1
            else:                               limit = 2
                
            from_state_set = from_db[si]
            n              = len(from_state_set) 

            if n < limit: self.linear_db[si] = LinearStateInfo()
            else:         self.mouth_db[si]  = MouthStateInfo(from_state_set)

    def determine_scr_by_state(self):
        """Determine for each state the set of concerned registers (sCR) and
        store it in the StateInfo object.
        
        REQUIRES: previous call to '.categorize()'
        """
        for si, scr in self.recipe_type.get_scr_by_state_index(self._sm):
            self.get_state_info(si).scr = scr

    def setup_initial_springs(self):
        """Finds the states in the state machine that comply to the condition
        of a 'spring' as defined in 00-README.txt. It determines the recipe for
        those springs and adds them to the databases.

        RETURNS: list of state indices of initial spring states.
        """
        result = set()
        for si, recipe in self.recipe_type.initial_spring_recipe_pairs(self._sm, self.mouth_db):
            # A 'mouth' can never be an initial spring
            assert si not in self.mouth_db
            self.set_recipe(si, recipe)
            result.add(si)
        return result

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

    def resolve_dead_locks(self, UnresolvedMouthStateSet):
        """For the given set of unresolved mouth states, implement the 'restore
        all' recipe. That means, that the value of registers is determined at
        run-time upon entry into the state, stored in an auxiliary register
        and restored upon need in recipes.

        Using this approach to resolve unresolved mouth states is safe to
        deliver a complete solution.
        """
        self._interfere_virtually(UnresolvedMouthStateSet)
        resolved_set = self.resolve(UnresolvedMouthStateSet)
        assert resolved_set == UnresolvedMouthStateSet

        self._dead_locks_fine_tuning(resolved_set)

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

    def get_horizon(self, UnresolvedMouthStateSet):
        """Horizon: Definition see "00-README.txt".
        Brief: The horizon is a subset of dead-lock states that have at
        least one determined entry.  In "00-README.txt" it is proven that
        such states always exist.

        RETURNS: List of indeces of horizon states.
        """
        return [
            si for si in UnresolvedMouthStateSet
               if self.mouth_db[si].entry_recipes_one_determined()
        ]

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
                      if self.mouth_db[si].entry_reicpes_all_determined())

    def _interfere(self, CandidateSet, 
                   GetEntryRecipeDb=lambda si, mouth: mouth.entry_recipe_db):
        """Perform interference of mouth states. Find for each state index the
        MouthInfo and determine the interfered recipe by '.recipe_type', i.e.
        according to the investigated behavior.

        MouthInfo.recipe:   Recipe of resolved mouth state.
        """
        for si, info in ((si, self.mouth_db[si]) for si in CandidateSet):
            entry_recipe_db       = GetEntryRecipeDb(si, info)
            required_register_set = self.recipe_type.get_RR_superset(self._sm, si, 
                                                                     self.predecessor_db)
            assert type(required_register_set) == set

            info.recipe,            \
            determined_register_set = self.recipe_type.interfere(entry_recipe_db)
            assert determined_register_set is not None

            info.undetermined_register_set = required_register_set.difference(determined_register_set)

    def _interfere_virtually(self, UnresolvedMouthStateSet):
        """Performs a 'virtual' interference where undetermined entry recipes
        are derived from 'op(i)(RestoreAll)'. That is, the concatination of the
        restore all recipe with the operations of the current mouth state.
        """
        def prepare(StateIndex, PresentRecipe, SingleEntry):
            """Provide recipe for virtual entry recipe database. 
            
            RETURN: PresentRecipe  -- if PresentRecipe is determined 
                    op(i)(RA(i))   -- else.
            """
            if PresentRecipe is not None: 
                recipe = PresentRecipe
            else:
                RA = self.recipe_type.RestoreAll(StateIndex)
                recipe = self.recipe_type.accumulate(RA, SingleEntry)

            return recipe

        def get_virtual_entry_recipe_db(si, mouth):
            """Generate a virtual entry recipe database from '.entry_recipe_db'
            where each *undetermined* entry recipe is set to 
            
                                   op(i)(RA(i))
                              
            That is, the state's operation 'op(i)' is applied to the 'restore 
            all' recipe. This database is NOT set in 'mouth'!
            """
            assert mouth.mouth_f()
            single_entry = self._sm.states[si].single_entry
            result = dict(
                (from_si, prepare(si, recipe, single_entry))
                for from_si, recipe in mouth.entry_recipe_db.iteritems()
            )
            return result

        self._interfere(UnresolvedMouthStateSet, 
                        GetEntryRecipeDb = get_virtual_entry_recipe_db)

    def _dead_locks_fine_tuning(self, UnresolvedMouthStateSet):
        """
        Assume that 'resolve_dead_locks()' specified a complete state machine
        by recipes. Some of those recipes may still be improved, because now
        mouth states have determined entry recipes and may therefore perform
        interference.

        If this interference results in a more specific recipe, then it may be
        propagated through accumulation. All subsequent states (until the next
        mouth state) receive a new more specific recipe.

        IMPORTANT: At any point in time, the state machine description remains
                   CORRECT. The algorithm only develops more specific, more 
                   simple recipes for some states.
        """
        def scr_db_get(Frontier, MouthDb):
            """RETURNS: A map from state index to set of undetermined registers.
            """
            return dict(
                (si, MouthDb[si].undetermined_register_set)
                for si in Frontier
            )

        def scr_db_get_springs(scr_db, Frontier, MouthDb):
            """RETURNS: Set of states where further accumulation starts.

            Those are the states for which a more specific recipe could be 
            determined through interference.
            """
            return [
                si 
                for si in Frontier
                if len(MouthDb[si].undetermined_register_set) < len(scr_db[si])
            ]

        frontier = self.get_horizon(UnresolvedMouthStateSet)
        done_set = set()
        while frontier:
            # TERMINATION: If there are no new states reached by simplified
            #              recipes. 
            # Infinite iteration is obstructed. Relying on the 'done_set' a 
            # state can at max. be treated once. The number of states is finite.
            # Thus the number of iterations is finite.
            scr_db = scr_db_get(frontier, self.mouth_db)
            self._interfere(frontier)

            # The elements of the horizon, that produce a more specific output
            # are used to promote a simplified recipe.
            stable_recipe_state_set = scr_db_get_springs(scr_db, frontier, 
                                                         self.mouth_db)
            reached_set = self._accumulate(stable_recipe_state_set)
            done_set.update(stable_recipe_state_set)

            # New frontier: Those states which 
            #   -- have been reached by simplified recipes,
            #   -- are not yet treated, and 
            #   -- are part of the UnresolvedMouthStateSet (all of them should).
            frontier = [
                si for si in reached_set 
                   if si not in done_set and si in UnresolvedMouthStateSet
            ]
            
    def get_Entry(self, StateIndex):
        """Generates an 'state.Entry' object for the state of the given index.

        RETURNS: Dictionary:

                      'from_state_index' ---> OpList
        """
        info = self.get_state_info(StateIndex)
        if info.mouth_f(): return self.recipe_type.get_mouth_Entry(info)
        else:              return self.recipe_type.get_linear_Entry(info)

    def get_DropOut(self, StateIndex):
        """Generates a 'state.DropOut' object for the state of the given index.

        RETURNS: OpList
        """
        self.recipe_type.get_DropOut(self.get_state_info(StateIndex))

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
        CurrStateIndex, CurrRecipe = Args
        curr_state = self.examiner._sm.states[CurrStateIndex]

        # Termination Criteria:
        # (1) State  = Terminal: no transitions, do further recursion. 
        #                        (Nothing needs to be done to guarantee that)
        # NOT: (2) Target is determined  => No entry!
        # (3) Target is Mouth State => No entry!
        todo = []
        for target_index in curr_state.target_map.iterable_target_state_indices():
            if target_index is None: continue
            target_info = self.examiner.get_state_info(target_index)
            target      = self.examiner._sm.states[target_index]
            accumulated = self.examiner.recipe_type.accumulate(CurrRecipe, 
                                                               target.single_entry)
            if target_info.mouth_f():        
                # Mouth state ahead => accumulate, but do NOT enter!
                target_info.entry_recipe_db[CurrStateIndex] = accumulated
                self.mouths_touched_set.add(target_index)
                continue # (3) terminal 
            else:
                # Linear state ahead => accumulate and go further
                target_info.recipe = accumulated
                todo.append((target_index, target_info.recipe))

        if not todo: return None
        else:        return todo

    def on_finished(self, node):
        pass


