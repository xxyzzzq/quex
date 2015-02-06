"""
PURPOSE: Implementation of the 'Recipe-Based-Optimization' as described in the
         file ./doc/main.tex.

         [DOC] --> means the documentation located in ./doc
________________________________________________________________________________

NOTE: A significant amount of effort has been put into the development of the
      documentation in order to derive process details and to proof the 
      correctness of the approach. Reading the documents may take two hours. 
      However, the provided knowledge is key to understand this code.

(C) Frank-Rene Schaefer

ABSOLUTELY NO WARRANTY
________________________________________________________________________________
"""
from   quex.engine.state_machine.core            import StateMachine
from   quex.engine.analyzer.examine.recipe_base  import Recipe
from   quex.engine.analyzer.examine.state_info   import LinearStateInfo, \
                                                        MouthStateInfo
from   quex.engine.misc.tree_walker              import TreeWalker
from   quex.engine.misc.tools                    import all_true, typed

from   itertools import chain

@typed(SM=StateMachine)
def do(SM, RecipeType):
    """Takes a 'single-entry state machine' and derives an optimized 'multi-
    entry state machine' that behaves identical from an outside view [DOC].
    
    RecipeType -- derived from recipe_base.Recipe

    This type controls procedure elements related to an 'investigated behavior'
    [DOC]. Examples of investigated behavior are: acceptance behavior, line and
    column number counting, check-sum computation.
    """
    assert issubclass(RecipeType, Recipe)
        
    examiner = Examiner(SM, RecipeType)

    # Categorize states:
    #    .linear_db: 'linear states' being entered only from one state.
    #    .mouth_db:  'mouth states' being entered from multiple states.
    examiner.categorize()

    # Categorize => StateInfo-s are in place.
    examiner.determine_required_sets_of_variables()
    
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
    # the theory in "[DOC]".
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
        self._sm              = SM
        self.recipe_type      = RecipeType
        self.__predecessor_db = None

        self.linear_db   = {}  # map: state index --> LinearStateInfo
        self.mouth_db    = {}  # map: state index --> MouthStateInfo

    @property
    def predecessor_db(self):
        if self.__predecessor_db is None:
            self.__predecessor_db = self._sm.get_predecessor_db()
        return self.__predecessor_db

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

    def determine_required_sets_of_variables(self):
        """Determine for each state the set of concerned registers (sCR) and
        store it in the StateInfo object.
        
        REQUIRES: previous call to '.categorize()'
        """
        db = self.recipe_type.get_required_variable_superset_db(self._sm, self.predecessor_db, self.successor_db)

        for si, required_set_of_variables in db.iteritems():
            self.get_state_info(si).required_set_of_variables = required_set_of_variables

    def is_operation_constant(self, TheSingleEntry, VariableId=None, StateIndex=None):
        """An operation upon entry into a state is 'constant', if it does not
        depend on a setting of the required variables in that state.  The
        'single_entry' member of a single-entry state represents the concept of an
        operation 'op(i)' from [DOC]. Refer to [DOC] for the precise concept of
        constant operations.

        RETURNS: True  -- if the operation is constant
                 False -- if not.
        """
        if VariableId is None:
            for variable_id in self.get_state_info(StateIndex).required_set_of_variables:
                if not self.is_operation_constant(TheSingleEntry, variable_id):
                    return False
            return True

        # (1) An operation 'op(i)' that does not influence 'v' is not constant 
        #     (see discussion in [DOC])
        for cmd in TheSingleEntry: 
            if cmd.assigns(VariableId): break
        else:
            # There is a variable that is not assigned by 'op(i)'
            # => 'op(i)' is not constant
            return False

        # (2) An operation that relies on a previous setting of 'v' is not constant
        #
        for cmd in TheSingleEntry: 
            if cmd.requires(VariableId): return False
        return True

    def setup_initial_springs(self):
        """Finds the states in the state machine that comply to the condition
        of a 'spring' as defined in [DOC]. It determines the recipe for
        those springs and adds them to the databases.

        RETURNS: list of state indices of initial spring states.
        """
        result = set()
        for si, state in self._sm.states.iteritems():
            if not self.is_operation_constant(state.single_entry, si): continue
            recipe = self.recipe_type.accumulation(None, state.single_entry)
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
            self._interference(mouths_ready_set)

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
        remainder = UnresolvedMouthStateSet
        horizon   = self.get_horizon(remainder)
        while horizon:
            self._cautious_interference(horizon)
            remainder    = self.resolve(horizon)
            horizon      = self.get_horizon(remainder)

        self._dead_locks_fine_adjustment(UnresolvedMouthStateSet)

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
        """Horizon: Definition see "[DOC]".
        Brief: The horizon is a subset of dead-lock states that have at
        least one determined entry.  In "[DOC]" it is proven that
        such states always exist.

        RETURNS: List of indeces of horizon states.
        """
        return set(
            si for si in UnresolvedMouthStateSet
               if self.mouth_db[si].entry_recipes_one_determined()
        )

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

    def _interference(self, CandidateSet): 
        """Perform interference of mouth states. Find for each state index the
        MouthInfo and determine the interfered recipe by '.recipe_type', i.e.
        according to the investigated behavior.

        MouthInfo.recipe:   Recipe of resolved mouth state.
        """
        for si in CandidateSet:
            mouth = self.get_state_info(si)
            mouth.recipe, \
            mouth.homogeneity_db = self.recipe_type.interference(mouth)

    def _cautious_interference(self, HorizonStateSet):
        """Cautious interferences, as described in [DOC] may be implemented by 
        setting 'undetermined recipes' (also defined in [DOC]) at the place of 
        entry recipes. Then, inter
        """
        for si in CandidateSet:
            mouth = self.get_state_info(si)
            mouth.recipe, \
            mouth.homogeneity_db = self.recipe_type.cautious_interference(mouth)

    def _dead_locks_fine_adjustment(self, OriginalDeadLockSet):
        """Fine adjustment, according to [DOC], means that components of
        constant entry recipes are identified.

        OriginalDeadLockSet -- set of states that were originally dead-locks.
        """

        while 1 + 1 == 2:
            improved_state_set = improve(OriginalDeadLockSet)
            if not improved_state_set: break
            self.resolve(improved_state_set)

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
        # * State  = Terminal: no transitions, no further recursion. 
        #                      (Nothing needs to be done to guarantee that)
        # * Target is Mouth State => No entry!
        # * Target is Spring      => No entry!
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
                continue # terminal condition
            elif target.spring_f():
                continue # terminal condition
            else:
                # Linear state ahead => accumulate and go further
                target_info.recipe = accumulated
                todo.append((target_index, target_info.recipe))

        if not todo: return None
        else:        return todo

    def on_finished(self, node):
        pass


