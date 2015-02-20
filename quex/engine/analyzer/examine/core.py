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

    # Determine states from where a walk along linear states can begin.
    springs = examiner.setup_initial_springs()
    if not springs:
        remainder = set(examiner.mouth_db.iterkeys())
        springs   = examiner.prepare_springs_of_horizon(remainder)

    while springs:
        remainder = examiner.resolve(springs)
        springs   = examiner.prepare_springs_of_horizon(remainder)
        
    # Double check, that the result makes sense.
    examiner.assert_consistency()

    return examiner.linear_db, examiner.mouth_db

class Examiner:
    """Maintainer of data and provider of operations for the linear state and
    mouth state analysis. Its purpose is to support the sequential process 
    implemented in the global '.do()' function.
    """
    def __init__(self, SM, RecipeType):
        self._sm            = SM
        self.recipe_type    = RecipeType
        self.predecessor_db = self._sm.get_predecessor_db()
        self.successor_db   = self._sm.get_successor_db(self.predecessor_db)

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

    def determine_required_sets_of_variables(self):
        """Determine for each state the set of concerned registers (sCR) and
        store it in the StateInfo object.
        
        REQUIRES: previous call to '.categorize()'
        """
        db = self.recipe_type.get_required_variable_superset_db(self._sm, 
                                                                self.predecessor_db, 
                                                                self.successor_db)

        for si, required_variable_set in db.iteritems():
            print "#si, rvs:", si, required_variable_set
            self.get_state_info(si).required_variable_set = required_variable_set

    def is_operation_constant(self, TheSingleEntry, RequiredVariableSet):
        """An operation upon entry into a state is 'constant', if it does not
        depend on a setting of the required variables in that state.  The
        'single_entry' member of a single-entry state represents the concept of an
        operation 'op(i)' from [DOC]. Refer to [DOC] for the precise concept of
        constant operations.

        RETURNS: True  -- if the operation is constant
                 False -- if not.
        """
        for variable_id in RequiredVariableSet:
            if not self.is_operation_component_constant(TheSingleEntry, variable_id):
                return False
        return True

    def is_operation_component_constant(self, TheSingleEntry, VariableId):
        # (1) An operation 'op(i)' that does not influence 'v' is not constant 
        #     (see discussion in [DOC])
        for cmd in TheSingleEntry: 
            if VariableId in cmd.assigned_variable_ids(): break
        else:
            # There is a variable that is not assigned by 'op(i)'
            # => 'op(i)' is not constant
            return False

        # (2) An operation that relies on a previous setting of 'v' is not constant
        #
        for cmd in TheSingleEntry: 
            if VariableId in cmd.required_variable_ids(): return False
        return True

    def setup_initial_springs(self):
        """Finds the states in the state machine that comply to the condition
        of a 'spring' as defined in [DOC]. It determines the recipe for
        those springs and adds them to the databases.

        RETURNS: list of state indices of initial spring states.
        """
        assert set(self.mouth_db).isdisjoint(set(self.linear_db))

        self.determine_required_sets_of_variables()
    
        result = set()
        for si, state in self._sm.states.iteritems():
            rsov = self.get_state_info(si).required_variable_set
            if not self.is_operation_constant(state.single_entry, rsov): continue
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
        springs  = Springs
        done_set = set()
        while springs:
            for si in springs:
                self.get_state_info(si).spring_f = True

            # Derive recipes along linear states starting from springs.
            mouths_ready_set = self._accumulate(springs) 
            done_set.update(springs)

            # Mouth states where all entry recipes are set
            # => Apply 'interference' to determine their recipe.
            self._interference(mouths_ready_set)

            # The determined mouths become the springs for the linear walk
            # Only take NEW springs. 
            springs = mouths_ready_set.difference(done_set)

        # Return the set of still undetermined mouth states.
        return set(si for si, mouth in self.mouth_db.iteritems()
                      if not mouth.is_determined())

    def prepare_springs_of_horizon(self, UnresolvedMouthStateSet):
        """For the given set of unresolved mouth states, implement the 'restore
        all' recipe. That means, that the value of registers is determined at
        run-time upon entry into the state, stored in an auxiliary register
        and restored upon need in recipes.

        Using this approach to resolve unresolved mouth states is safe to
        deliver a complete solution.
        """
        horizon = self.get_horizon(UnresolvedMouthStateSet)

        # Cautious interference: apply interference with 'undetermined' 
        # recipes in horizon states. 
        for si in horizon:
            self._prepare_cautious_recipe(si)
        self._interference(horizon)
        return horizon

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

        Brief: The horizon is a subset of dead-lock states that have at least
        one determined entry.  In "[DOC]" it is proven that such states always
        exist, if dead-lock states exist.

        RETURNS: List of indeces of horizon states.
        """
        def condition(si):
            """According to its definition in [DOC], a state is a horizon state
            if it is undetermined (a dead-lock state) and has at least one 
            determined entry. This is the case, if it has at least one undeter-
            mined and at least one determined entry.
            """
            has_determined_f   = False
            has_undetermined_f = False
            for entry_recipe in self.get_state_info(si).entry_recipe_db.itervalues():
                if entry_recipe is None: has_undetermined_f = True
                else:                    has_determined_f   = True
                if has_determined_f and has_undetermined_f:
                    return True
            return False

        return set(
            si for si in UnresolvedMouthStateSet if condition(si)
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
            mouth.recipe,        \
            mouth.homogeneity_db = self.recipe_type.interference(mouth, si)

    def _prepare_cautious_recipe(self, StateIndex):
        """[DOC] describes the process of 'cautious interference' as a type of 
        interference, where it is assumed that all variables are stored upon
        entry and restored in the output recipe. It has been shown in [DOC]
        that a safe procedure to do so is to replace undetermined entries with 
        'cautious entries' consisting of a concatination of the undetermined
        recipe with the current states 'op(i)' (i.e. '.single_entry').

        Once, all undetermined entries are occupied, ordinary interference is
        performed. 
        """
        # A horizon state MUST be a mouth state!
        mouth               = self.mouth_db[StateIndex]
        print "#mouth_id:", StateIndex, id(mouth), id(self.get_state_info(StateIndex))

        # According to [DOC] use 'op(i) o UndeterminedRecipe' as entry recipe
        # before interference.
        undetermined_recipe = self.recipe_type.undetermined(mouth.required_variable_set)
        single_entry        = self._sm.states[StateIndex].single_entry
        cautious_recipe     = self.recipe_type.accumulation(undetermined_recipe,
                                                            single_entry)
        print "#cautious:", cautious_recipe

        # Replace any undetermined entry recipe with the 'cautious recipe'.
        for predecessor_si, entry in mouth.entry_recipe_db.items():
            if entry is not None: continue
            mouth.entry_recipe_db[predecessor_si] = cautious_recipe

    def assert_consistency(self):
        """After termination, every state must have a recipe assigned to it.
        """
        assert all_true(chain(examiner.linear_db.itervalues(), 
                              examiner.mouth_db.itervalues()), 
                        lambda x: x.is_determined()) 
    

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
            accumulated = self.examiner.recipe_type.accumulation(CurrRecipe, 
                                                                 target.single_entry)
            if target_info.mouth_f():        
                # Mouth state ahead => accumulate, but do NOT enter!
                target_info.entry_recipe_db[CurrStateIndex] = accumulated
                self.mouths_touched_set.add(target_index)
                continue # terminal condition
            elif target_info.spring_f:
                continue # terminal condition
            else:
                # Linear state ahead => accumulate and go further
                target_info.recipe = accumulated
                todo.append((target_index, target_info.recipe))

        if not todo: return None
        else:        return todo

    def on_finished(self, node):
        pass


