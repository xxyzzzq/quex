from quex.engine.analyzer.examiner.recipe_base import Recipe
from quex.engine.misc.enum                     import Enum

class Recipe4Test(Recipe):
    """Base class for SCR recipes. The general recipe depends on:

        -- The current state.
        -- Constants which can be pre-determined.
        -- Register contents which are developed at run-time.

    See 00-README.txt the according DEFINITION.
    """
    SCR = (E_R.ColumnCount, E_R.LineCount) # Just as an example ...
    #                                      # They ARE NOT treated here
    #                                      # according their meaning.

    @staticmethod
    def get_scr_by_state_index(SM):
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
        return ((state_index, Recipe4Test.SCR)
                for state_index in SM.states.iterkeys())

    @staticmethod
    def get_initial_springs(SM):
        """The term 'spring' has been defined in 00-README.txt as a state where
        the walk along linear states may begin. An initial spring is a state 
        where the entry operations determine all registers of the SCR while making
        all previous history redundant.

        RETURNS: State inidices of initial springs.
        """
        return SM.init_state_index

    @staticmethod
    def from_accumulation(Recipe, LinearState):
        """RETURNS: An accumulated action that expresses the concatenation of
                    the given Recipe, with the operation at entry of LinearState.

        The resulting accumulated action determines the setting of SCR(i) after
        the linear state has been entered.
        """
        assert False

    @staticmethod
    def from_interference(RecipeIterable, MouthState):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes actions at different entries into a MouthState.
        """
        assert False

    @staticmethod
    def from_interference_in_dead_lock_group(DeadLockGroup):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes of states of a dead lock group.
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
    
