"""PURPOSE:

This file defines the base class for all 'recipes' as defined in [DOC].
No object is supposed to be instantiated of class 'Recipe'. Instead, concrete 
classes need to be derived from it. The derived concrete classes can then 
instantiate objects. 

The derived concrete class of 'Recipe' implements the specification of a 
particular considered behavior. 

The 'Recipe' class defines an 'interface' in the Java sense, and an 'abstract
class' in the C++ sense. It consists of '@staticmethod'-s and member functions.
The derived class must follow the same exact scheme. Only then, the derived
recipe fits the algorithm of analysis.

The appropriate way to add a new investigated behavior is to copy the class 
'Recipe', rename it, derive the new-named class from 'Recipe' and fill its
functions with meaningful content.

(C) Frank-Rene Schaefer
"""
from quex.engine.misc.tools  import UniformObject, E_Values
from quex.blackboard         import E_StateIndices

class Recipe:
    """Base class for SCR recipes. The general recipe depends on:

        -- The current state.
        -- Constants which can be pre-determined.
        -- Register contents which are developed at run-time.

    A derived class MUST implement:

       .__init__(): taking a list of SCR relevant operations.

    A derived class CAN implement:

       .get_SCR_operations(): extracts those operations out of a state
              entry which are relevant to the SCR.

       .from_spring(): Constructs a recipe from a spring states.

       .get_SCR_by_state_index(): generator that provides an iterable
              over pairs of (state index, SCR). That is usefull, if the
              SCR differs from state to state.

       .get_initial_springs(): determines the set of initial springs. By
              default, the sole initial spring is simply the init state.

    See [DOC] the according DEFINITION.
    """
    @staticmethod
    def _snap_shot_map_interference(Mouth, StateIndex):
        """This function supports the 'interference' procedure. When an entry recipe
        with respect to a variable 'v' is not homogeneous, then the variable's value
        must be computed upon entry and the snapshot map must contain the current 
        state as the 'snapshot state', i.e. the state where the snapshot has been 
        taken. 

        HomogeneityDb: 
            
            variable_id --> True -- if entry expression for variable_id
                                    is homogeneous
                            False -- if it is not

        implement_entry_operation_db:

            variable_id --> flag indicating whether 'v' needs to be 
                            computed and stored in auxiliary variable.

        PrototypeSnapshotMap:

            Snapshot map of any entry recipe. It is considered only for those 
            'variable_id'-s which are homogeneous.

        ADAPTS:  implement_entry_operation_db

        RETURNS: snapshot map

            variable_id --> state index where the snapshot has been taken.
                            None, if the variable is not restored from 'A(v)'.
        """
        snapshot_map   = {}
        homogeneity_db = {}
        for variable_id in Mouth.required_variable_set:

            uniform_object = UniformObject.from_iterable(
                 recipe.snapshot_map[variable_id]
                 for recipe in Mouth.entry_recipe_db.itervalues()
            )

            if uniform_object.plain_content() != E_Values.VOID: # Homogeneity
                assert    uniform_object.content is None \
                       or isinstance(uniform_object.content, (int, long))
                snapshot_map[variable_id]   = uniform_object.content
                homogeneity_db[variable_id] = True
            else:                                               # Inhomogeneity
                snapshot_map[variable_id]   = StateIndex
                homogeneity_db[variable_id] = False

        return snapshot_map, homogeneity_db

    def cautious_interference(cls, Mouth):
        """According to [DOC], cautious interference may be entirely 
        implemented relying on 'undetermined recipes', 'accumulation', 
        and normal 'interference'. Thus, cautious interference is implemented
        in the base class of recipes.

        NOTE: Nothing is done to the homogeneity_db, because its adaption
              will be a natural consequence of the undetermined recipe.
        """
        assert Mouth.mouth_f()
        required_variable_set = Mouth.required_variable_set

        # According to [DOC] use 'op(i) o UndeterminedRecipe' as entry recipe
        # before interference.
        undetermined_recipe = self.recipe_type.undetermined(required_variable_set)
        entry_recipe        = self.recipe_type.accumulate(undetermined_recipe,
                                                          SingleEntry)

        for predecessor_si, entry in Mouth.entry_recipe_db.items():
            if entry is None: 
                Mouth.entry_recipe_db[predecessor_si] = entry_recipe

        return cls.interfere(Mouth)

    @classmethod
    def apply_inhomogeneity(cls, snapshot_map, homogeneity_db, VariableId, StateIndex):
        """When inhomogeneity for a variable 'VariableId' is detected, then the
        'v' is stored in 'A(v)', i.e. the snapshot map for 'v' is the current state.
        The homogeneity_db for the given variable must be set to 'False'.
        """
        snapshot_map[VariableId]   = StateIndex
        homogeneity_db[VariableId] = False

    @staticmethod
    def tag_successors(db, si, SuccessorDb, VariableId):
        db[si].add(VariableId)
        for successor_si in SuccessorDb[si]:
            db[successor_si].add(VariableId)

    @staticmethod
    def cmd_iterable(SM, CmdType):
        """Iterate over all states and commands which are concerned of the
        given command type.
        """
        for si, state in SM.states.iteritems():
            for cmd in state.single_entry.get_iterable(CmdType):
                yield si, cmd

    @classmethod
    def get_SCR_operations(cls, TheState):
        """For a given state, it extracts the operations upon entry which 
        modify registers of the SCR. 

        RETURNS: A list of operations on the SCR.
        """
        return [ op for op in TheState.single_entry if op.modifies(cls.SCR) ] 

    @classmethod
    def get_scr_by_state_index(cls, SM):
        """Determines terminals in the state machine which absolutely require
        some information about a set of registers (SCR) for the investigated
        behavior. The set is not concerned of determination happening during
        analysis or at run-time. 

        This is the default implementation, which simply returns the class'
        SCR for all states.

        YIELDS: (state index, SCR)
        """
        for si in SM.states:
            yield si, cls.SCR

    @classmethod
    def initial_spring_recipe_pairs(cls, Sm, MouthDb):
        """The term 'spring' has been defined in [DOC] as a state where
        the walk along linear states may begin. An initial spring is a state 
        where the entry operations determine all registers of the SCR while making
        all previous history redundant.

        This is the default implementation, which simply returns the init state
        of the state machine--a safe solution.

        RETURNS: list of (si, recipe)
        
        where 'si' is the state index of a spring and 'recipe' its recipe. This
        default implementation is a safe approach, in case that it is difficult
        to make assumptions about states deeper insider the state machine.
        """
        si    = Sm.init_state_index
        mouth = MouthDb.get(si)
        if mouth is None:
            recipe = cls.accumulate(None, Sm.get_init_state().single_entry)
            return [(si, recipe)]
        else:
            entry_recipe = cls.accumulate(None, Sm.get_init_state().single_entry)
            mouth.entry_recipe_db[E_StateIndices.NONE] = entry_recipe
            # A mouth state can never be an initial spring
            # => Analysis starts with dead-lock analysis
            return []

