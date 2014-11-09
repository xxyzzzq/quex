from quex.engine.analyzer.examiner.core import Recipe
from quex.engine.misc.enum              import Enum

E_SOV_Test = Enum("X", "Y", "Z")

class TestRecipe(Recipe):
    """Implementation of class 'Recipe' for testing purposes.
    """
    @staticmethod
    def get_terminal_SOV_db(SM):
        """Determines terminals in the state machine which absolutely require
        some information about a set of variables (SOV) for the investigated
        behavior. The set is not concerned of determination happening during
        analysis or at run-time. 

        Only 'terminals' need to be specified, because the SOV(i) for each 
        state 'i' is determined by BACK-PROPAGATION of needs.

        RETURNS: defaultdict(set): state index --> set of variables

        The 'variables' are best determined in form of 'Enum' values. The 
        return type must be 'defaultdict(set)' so that it can be easily 
        extended by further processing.
        """
        assert False

    @staticmethod
    def get_SOV_operation(TheState):
        """Extracts from a given state machine state the operation on the SOV, 
        i.e. the set of variables that describe the behavior (see 00-README.txt).

        RETURNS: A description of the operations on the SOV upon entry into 
                 'TheState'.
        """
        assert False

    @staticmethod
    def is_spring(TheState, SOV):
        """RETURNS: True  -- if TheState complies with the requirements of a 
                             spring state.
                    False -- else.

        In a spring the Recipe(i) must be determined. That is, as soon as this
        state is entered any history becomes unimportant. The setting of the
        SOV(i) can be determined from an Recipe(i).
        """
        assert False

    @staticmethod
    def from_spring(SpringState):
        """RETURNS: An accumulated action that determines the setting of the
                    SOV(i) after the SpringState has been entered.
        """
        assert False

    @staticmethod
    def from_accumulation(Recipe, LinearState):
        """RETURNS: An accumulated action that expresses the concatenation of
                    the given Recipe, with the operation at entry of LinearState.

        The resulting accumulated action determines the setting of SOV(i) after
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
    def from_interference_for_dead_lock_group(DeadLockGroup):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes of states of a dead_lock group.
        """
        assert False
