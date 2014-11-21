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

    See 00-README.txt the according DEFINITION.
    """
    @classmethod
    def get_SCR_operation(cls, TheState):
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
        return cls(self.get_SCR_operation(SpringState.single_entry))

    @staticmethod
    def get_SCR_terminal_db(SM):
        """Determines terminals in the state machine which absolutely require
        some information about a set of registers (SCR) for the investigated
        behavior. The set is not concerned of determination happening during
        analysis or at run-time. 

        Only 'terminals' need to be specified, because the SCR(i) for each 
        state 'i' is determined by BACK-PROPAGATION of needs.

        RETURNS: defaultdict(set): state index --> set of registers

        The 'registers' are best determined in form of 'Enum' values. The 
        return type must be 'defaultdict(set)' so that it can be easily 
        extended by further processing.
        """
        assert False

    @staticmethod
    def get_initial_springs(SM):
        """The term 'spring' has been defined in 00-README.txt as a state where
        the walk along linear states may begin. An initial spring is a state 
        where the entry operations determine all registers of the SCR while making
        all previous history redundant.

        RETURNS: State inidices of initial springs.
        """
        assert False

    @staticmethod
    def from_accumulation(Recipe, Operation):
        """RETURNS: An accumulated action that expresses the concatenation of
                    the given Recipe, with the operation at entry of LinearState.

        The resulting accumulated action determines the setting of SCR(i) after
        the linear state has been entered.
        """
        assert False

    @staticmethod
    def from_interference(RecipeIterable):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes actions at different entries into a MouthState.

        The resulting recipe is applied ONLY to the mouth state of concern--
        in contrast to what happens in 'from_interference_in_dead_lock_group()'.
        """
        assert False

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
    
