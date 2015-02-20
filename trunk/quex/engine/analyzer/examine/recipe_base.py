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

            print "#variable_id:", variable_id
            print "#values:     ", [
                 recipe.snapshot_map.get(variable_id)
                 for recipe in Mouth.entry_recipe_db.itervalues()
            ]
            uniform_object = UniformObject.from_iterable(
                 recipe.snapshot_map.get(variable_id)
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

    @classmethod
    def apply_inhomogeneity(cls, snapshot_map, homogeneity_db, VariableId, StateIndex):
        """When inhomogeneity for a variable 'VariableId' is detected, then the
        'v' is stored in 'A(v)', i.e. the snapshot map for 'v' is the current state.
        The homogeneity_db for the given variable must be set to 'False'.
        """
        snapshot_map[VariableId]   = StateIndex
        homogeneity_db[VariableId] = False

    @staticmethod
    def tag_iterable(db, StateIndexIterable, VariableId):
        """Add VariableId to every dictionary entry 'db[si]' where 'si' is
        provided by the 'StateIndexIterable'.
        """
        for si in StateIndexIterable:
            db[si].add(VariableId)

    @staticmethod
    def cmd_iterable(SM, CmdType):
        """Iterate over all states and commands which are concerned of the
        given command type.
        """
        for si, state in SM.states.iteritems():
            for cmd in state.single_entry.get_iterable(CmdType):
                yield si, cmd

