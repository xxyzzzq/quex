from   quex.core_engine.state_machine.transition import Transition, EpsilonTransition


class TransitionMap:
    def __init__(self):
        self.__db = {} # [target index] --> [trigger set that triggers to target]
