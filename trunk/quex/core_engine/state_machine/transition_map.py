from   quex.core_engine.state_machine.transition import Transition, EpsilonTransition


class TransitionMap:
    def __init__(self):
        self.__db = {}               # [target index] --> [trigger set that triggers to target]
        self.__db_change_f = False
        #
        self.__cache_transition_list      = []
        self.__cache_combined_trigger_set = NumberSet()

    def is_empty(self):
        return len(self.__db) == 0

    def get_list(self):
        if self.__db_change_f == False:
            return self.__cache_transition_list

        result = []
        for target_index, trigger_set in self.__db.items():
            result.append(Transition(trigger_set, target_index))

        self.__cache_transition_list = result
        return result

    def get_combined_trigger_set(self):
        if self.__db_change_f == False:
            return self.__cache_combined_trigger_set

        result = NumberSet()
        for trigger_set in self.__db.values():
            result.unite_with(trigger_set)

        self.__cache_combined_trigger_set = result
        return result

    def get_target_state_index_list(self):
        return self.__db.keys()

    def get_map(self):
        return self.__db
