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

class Recipe:
    """Base class for SCR recipes. The general recipe depends on:

        -- The current state.
        -- Constants which can be pre-determined.
        -- Register contents which are developed at run-time.

    A derived class MUST implement:

       .__init__(): taking a list of SCR relevant operations.

       .from_accumulation(): Concatinating a recipe with new SCR relevant
              operations in a linear state.

       .from_interference(): Building a recipe from the interference of 
              recipes in a mouth state.

       .from_interference_in_dead_lock_group(): Building a recipe for
              a dead-lock state group.

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
    def from_spring(cls, SpringState):
        """RETURNS: A recipe that determines the setting of the SCR(i) after 
        the SpringState has been entered.
        """
        return cls(self.get_SCR_operations(SpringState.single_entry))

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

    @staticmethod
    def get_initial_springs(SM):
        """The term 'spring' has been defined in 00-README.txt as a state where
        the walk along linear states may begin. An initial spring is a state 
        where the entry operations determine all registers of the SCR while making
        all previous history redundant.

        This is the default implementation, which simply returns the init state
        of the state machine--a safe solution.

        RETURNS: State inidices of initial springs.
        """
        return SM.init_state_index

    @staticmethod
    def from_accumulation(Recipe, SingeEntry):
        """RETURNS: Recipe 
        
        The Recipe expresses how to compute the SCR in a linear state where
        the previous recipe is extended by the operations at state entry
        (the 'single_entry' object).
        """
        assert False # --> derived class

    @staticmethod
    def from_interference(RecipeIterable):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes actions at different entries into a MouthState.

        The resulting recipe is applied ONLY to the mouth state of concern--
        in contrast to what happens in 'from_interference_in_dead_lock_group()'.
        """
        assert False # --> derived class

    @staticmethod
    def from_interference_in_dead_lock_group(DeadLockGroup):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes of states of a dead_lock group.

        The important difference to 'from_interference()' is that the resulting 
        recipe is applied to MULTIPLE states.
        """
        assert False

    def get_drop_out_OpList(self):
        """With a given Recipe(i) for a state 'i', the action upon state machine
        exit can be determined.

        RETURNS: A OpList that corresponds self.
        """
        assert False
    
    def get_entry_OpList(self, NextRecipe):
        """Consider the NextRecipe with respect to self. Some contents may 
        have to be stored in registers upon entry into this state. 

        RETURNS: A OpList that allows 'InterferedRecipe' to operate after 
                 the state.

        This is particularily important at mouth states, where 'self' is an 
        entry into the mouth state and 'NextRecipe' is the accumulated action
        after the state has been entered.
        """
        assert False
    
