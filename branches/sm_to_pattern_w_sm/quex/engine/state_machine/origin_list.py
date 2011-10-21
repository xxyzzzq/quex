from quex.engine.state_machine.state_core_info import StateCoreInfo
from quex.blackboard import E_PreContextIDs, E_PostContextIDs
from itertools import ifilter

class StateOriginList(object):
    __slots__ = ('__list')

    def __init__(self, List=None):
        if List is None: self.__list = []
        else:            self.__list = List

    def clone(self):
        return StateOriginList([x.clone() for x in self.__list])

    def is_equivalent(self, Other):
        assert False
        # Loop over all origins in list and search for counterparts in Other
        for origin in self.__list:
            # Is there an equivalent origin in Other?
            for counterpart in Other.__list:
                if origin.is_equivalent(counterpart): break
            else:
                return False 

        # Vice versa ...
        for origin in Other.__list:
            for counterpart in self.__list:
                if origin.is_equivalent(counterpart): break
            else:
                return False 

        return True

    def get_list(self):
        return self.__list

    def __iter__(self):
        for x in self.__list:
            yield x

    def __add(self, Origin):
        """Check if origin has already been mentioned, else append the new origin.
        """
        SM_ID = Origin.state_machine_id
        for same in (origin for origin in self.__list if origin.state_machine_id == SM_ID):
            same.merge(Origin)
            return
        self.__list.append(Origin.clone())

    def add(self, X, StateIndex, StoreInputPositionF=False, SelfAcceptanceF=False):
        """Add the StateMachineID and the given StateIdx to the list of origins of 
           this state.
           NOTE: The rule is that by default the 'input_position_store_f' flag
                 follows the acceptance state flag (i.e. by default any acceptance
                 state stores the input position). Thus when an origin is  added
                 to a state that is an acceptance state, the 'input_position_store_f'
                 has to be raised for all incoming origins.      
        """
        assert type(X) == long or X.__class__ == StateCoreInfo
        assert type(StateIndex) == long
        assert StoreInputPositionF is not None
            
        if X.__class__ == StateCoreInfo:
            self.__add(X.clone())
        else:
            self.__add(StateCoreInfo(StateMachineID      = X, 
                                     StateIndex          = StateIndex, 
                                     AcceptanceF         = SelfAcceptanceF,
                                     StoreInputPositionF = StoreInputPositionF))

    def merge(self, OriginList):
        for origin in OriginList: 
            self.__add(origin)

    def set(self, OriginList, ArgumentIsYoursF=False):
        assert type(OriginList) == list
        if ArgumentIsYoursF: self.__list = OriginList
        else:                self.__list = [ x.clone() for x in OriginList ]

    def clear(self):
        self.__list = []

    def is_empty(self):
        return len(self.__list) == 0

    def adapt(self, StateMachineID, StateIndex):
        """Adapts all origins so that their original state is 'StateIndex' in state machine
           'StateMachineID'. Post- and pre-condition flags remain, and so the store input 
           position flag.
        """
        for origin in self.__list:
            origin.state_machine_id = StateMachineID
            origin.state_index      = StateIndex 

    def delete_meaningless(self):
        """Deletes origins that are not concerned with one of the three:
           -- post-conditions
           -- pre-conditions/also trivials
           -- store input positions

           NOTE: This function is only to be used for single patterns not for
                 combined state machines. During the NFA to DFA translation
                 more than one state is combined into one. This maybe reflected
                 in the origin list. However, only at the point when the 
                 pattern state machine is ready, then the origin states are something
                 meaningful. The other information has to be kept.
                 
           NOTE: After applying this fuction to a single pattern, there should only
                 be one origin for each state.
        """
        self.__list = filter(lambda origin:
                                    origin.post_contexted_acceptance_f()            or
                                    origin.pre_context_id() != E_PreContextIDs.NONE or
                                    origin.input_position_store_f(),
                                    self.__list)

    def delete_dominated(self):
        """This function is a simplification in order to allow the Hopcroft Minimization
           to be more efficient. It 'simulates' the code generation where the first unconditional
           pattern matches. The remaining origins of a state are redundant.

           This function is to be seen in analogy with the function 'get_acceptance_detector'. 
           Except for the fact that it requires the 'end of core pattern' markers of post
           conditioned patterns. If the markers are not set, the store input position commands
           are not called properly, and when restoring the input position bad bad things happen 
           ... i.e. segmentation faults.
        """
        # NOTE: Acceptance origins sort before non-acceptance origins
        self.__list.sort(key=lambda x: (not x.is_acceptance(), x.state_machine_id))
        new_origin_list = []
        unconditional_acceptance_found_f = False
        for origin in self.__list:

            if origin.is_acceptance():
                # Only append acceptance origins until the first unconditional acceptance state 
                # is found. 
                if not unconditional_acceptance_found_f:
                    if origin.pre_context_id() == E_PreContextIDs.NONE:
                        unconditional_acceptance_found_f = True # prevent entering this part again
                    new_origin_list.append(origin)

            else:
                # Non-Acceptance origins do not harm in any way. Actually, the origins
                # with 'origin.input_position_store_f() == True' **need**
                # to be in there. See the comment at the entry of this function.
                new_origin_list.append(origin)

        self.__list = new_origin_list 

    def get_string(self):
        txt = " <~ "
        if len(self.__list) == 0: 
            return txt + "\n"
        for origin in self.__list:
            txt += repr(origin) + ", "
        txt = (txt[:-2] + "\n").replace("L","")     
        return txt
