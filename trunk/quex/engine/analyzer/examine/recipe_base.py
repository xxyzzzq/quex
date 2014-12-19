"""PURPOSE:

This file defines the base class for all 'recipes' as defined in 00-README.txt.
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
from quex.blackboard import E_StateIndices

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

    See 00-README.txt the according DEFINITION.
    """
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
        """The term 'spring' has been defined in 00-README.txt as a state where
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

