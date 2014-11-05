from quex.engine.state_machine.state_core_info import StateOperation
from quex.blackboard                           import E_PreContextIDs, E_IncidenceIDs

class SingleEntry(object):
    __slots__ = ('__list')

    def __init__(self):
        self.__list = []

    @staticmethod
    def from_iterable(Iterable):
        result = SingleEntry()
        result.merge(Iterable)
        return result

    def clone(self, ReplDbPreContext=None, ReplDbAcceptance=None):
        return SingleEntry.from_iterable(x.clone(ReplDbPreContext=ReplDbPreContext, ReplDbAcceptance=ReplDbAcceptance) for x in self.__list)

    def get_list(self):
        return self.__list

    def __iter__(self):
        for x in self.__list:
            yield x

    def __len__(self):
        return len(self.__list)

    def __add(self, Origin):
        """Check if origin has already been mentioned, else append the new origin.
        """
        # NOT: if not Origin.is_meaningful(): return
        #      We need even non-meaningful origins, to detect whether a state can be 
        #      combined with another during Hopcroft optimization.
            
        AcceptanceID = Origin.acceptance_id()
        if AcceptanceID != E_IncidenceIDs.MATCH_FAILURE:
            self.take_out_FAILURE()
        elif self.is_there_a_non_FAILURE():
            return

        for same in (origin for origin in self.__list if origin.acceptance_id() == AcceptanceID):
            same.merge(Origin)
            return
        self.__list.append(Origin.clone())

    def has_acceptance_id(self, AcceptanceID):
        for cmd in self:
            if cmd.__class__ == Accept and cmd.acceptance_id() == AcceptanceID:
                return True
        return False

    def has_begin_of_line_pre_context(self):
        for cmd in self:
            if cmd.__class__ == Accept and cmd.pre_context_id() == E_PreContextIDs.BEGIN_OF_LINE:
                return True
        return False

    def hopcroft_combinability_key(self):
        """Two states have the same hopcroft-combinability key, if and only if
        they are combinable during the initial state split in the hopcroft
        minimization. Criteria:
        
        (1) Acceptance states of a different origin constellation. The
            decision making about the winning pattern must be the same for all
            states of a state set that is possibly combined into one single
            state. 
        
            In particular, non-acceptance states can never be combined with
            acceptance states.
        
        (2) Two states of the same pattern where one stores the input position
            and the other not, cannot be combined. Otherwise, the input
            position would be stored in unexpected situations.

        The approach is the following: For each investigated behavior a a tuple
        of numbers can be derived that describes it uniquely. The tuple of all
        tuples is used during the hopcroft minimization to distinguish between
        combinable states and those that are not.
        """
        def acceptance_info():
            """Before the track analysis, the acceptance in a state is simple
            given by its precedence, i.e. its acceptance id. Thus, the sorted
            sequence of acceptance ids identifies the acceptance behavior.
            """
            return tuple(sorted(x.acceptance_id() 
                                for x in self if x.is_acceptance()
            ))

        # (2) Separate by Store-Input-Position Behavior
        def store_info():
            """The storing of input positions in registers is independent of its
            position in the command list (as long as it all happens before the increment
            of the input pointer, of course).

            The sorted list of position storage registers where positions are stored
            is a distinct description of the position storing behavior.
            """
            return tuple(sorted(x.acceptance_id() 
                                for x in self if x.input_position_store_f()))

        return (acceptance_info(), store_info())

    def add(self, X, StateIndex=None, 
            StoreInputPositionF   = False, 
            AcceptanceF           = False, 
            RestoreInputPositionF = False, 
            PreContextID          = E_PreContextIDs.NONE):
        """Add the StateMachineID and the given StateIdx to the list of origins of 
           this state.
           NOTE: The rule is that by default the 'input_position_store_f' flag
                 follows the acceptance state flag (i.e. by default any acceptance
                 state stores the input position). Thus when an origin is  added
                 to a state that is an acceptance state, the 'input_position_store_f'
                 has to be raised for all incoming origins.      
        """
        assert type(X) == long or X == E_IncidenceIDs.MATCH_FAILURE or X.__class__ == StateOperation
        assert StateIndex is None or type(StateIndex) == long
        assert StoreInputPositionF is not None
            
        if isinstance(X, StateOperation):
            self.__add(X.clone())
        else:
            self.__add(StateOperation(AcceptanceID          = X, 
                                      StateIndex            = StateIndex, 
                                      AcceptanceF           = AcceptanceF,
                                      PreContextID          = PreContextID,
                                      StoreInputPositionF   = StoreInputPositionF, 
                                      RestoreInputPositionF = RestoreInputPositionF))

    def merge(self, OriginIterable):
        for origin in OriginIterable: 
            self.__add(origin)

    def merge_list(self, OriginIterableIterable):
        for origin_iterable in OriginIterableIterable:
            self.merge(origin_iterable)

    def set(self, OriginList, ArgumentIsYoursF=False):
        assert type(OriginList) == list
        if ArgumentIsYoursF: 
            self.__list = OriginList
            return
        self.__list = []
        self.merge(OriginList)

    def clear(self):
        self.__list = []

    def delete_dominated(self):
        """Simplification to make Hopcroft Minimization more efficient. The first unconditional
        acceptance makes any lower priorized acceptances meaningless. 

        This function is to be seen in analogy with the function 'get_acceptance_detector'. 
        Except for the fact that it requires the 'end of core pattern' markers of post
        conditioned patterns. If the markers are not set, the store input position commands
        are not called properly, and when restoring the input position bad bad things happen 
        ... i.e. segmentation faults.
        """
        # NOTE: Acceptance origins sort before non-acceptance origins
        self.__list.sort(key=lambda x: (not x.is_acceptance(), x.acceptance_id()))
        new_origin_list                  = []
        unconditional_acceptance_found_f = False
        for origin in self.__list:
            if not origin.is_acceptance():
                new_origin_list.append(origin)  # Out of consideration. 
                continue

            # Only append acceptance origins until the first unconditional acceptance.
            if not unconditional_acceptance_found_f:
                if origin.pre_context_id() == E_PreContextIDs.NONE:
                    unconditional_acceptance_found_f = True # prevent entering this part again
                new_origin_list.append(origin)

        self.__list = new_origin_list 

    def get_string(self, OriginalStatesF=True):

        txt = "" 
        if len(self.__list) == 0: 
            return txt + "\n"

        for origin in self.__list:
            if   origin.is_acceptance():                          break
            elif origin.pre_context_id() != E_PreContextIDs.NONE: break
            elif origin.input_position_store_f():                 break
            elif origin.input_position_restore_f():               break
        else:
            # All origins are 'harmless'. Sort by acceptance_id for the 'camera'.
            for origin in sorted(self.__list, key=lambda x: x.acceptance_id()):
                ostr = origin.get_string() 
                if ostr: txt += "%s, " % ostr
            txt = (txt[:-2] + "\n").replace("L","")     
            return txt

        # for origin in sorted(self.__list, key=attrgetter("state_machine_id")):
        for origin in self.__list:
            ostr = origin.get_string() 
            if ostr: txt += "%s, " % ostr
        txt = (txt[:-2] + "\n").replace("L","")     
        return txt

    def take_out_FAILURE(self):
        L = len(self.__list)
        for i in xrange(L-1, -1, -1):
            if self.__list[i].acceptance_id() == E_IncidenceIDs.MATCH_FAILURE:
                del self.__list[i]

    def is_there_a_non_FAILURE(self):
        for origin in self.__list:
            if origin.acceptance_id() != E_IncidenceIDs.MATCH_FAILURE:
                return True
        return False

