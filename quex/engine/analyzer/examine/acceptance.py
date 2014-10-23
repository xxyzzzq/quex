from collections import namedtuple

class AcceptanceScheme_Element(object): 
    def __init__(self):
        self.pre_context     = PreContext
        self.position_offset = PositionOffset
        self.acceptance_id   = AcceptanceId
        self.accepting_state_index_list = [ AcceptingStateIndex ]
        self.storing_state_index_list   = [ StoringStateIndex ]

class AcceptanceScheme(tuple):
    def __new__(self, List):
        return 

    @staticmethod
    def concatinate(This, That):
        assert This.__class__ == AcceptanceScheme
        assert That.__class__ == AcceptanceScheme
        return tuple(This + That)

    @staticmethod
    def from_action_list(ActionList):
        return AcceptanceScheme(ActionList)


def termination(State, Transition):
    """RETURNS: True -- If the target state may be entered.
                False -- If not.
    """
