import quex.engine.state_machine.index         as     index
from   quex.engine.analyzer.core               import AnalyzerState
from   quex.engine.analyzer.state_entry_action import DoorID
from   quex.blackboard                         import E_StateIndices

class MegaState(AnalyzerState):
    """A MegaState is a state that implements more than one state at once.
       Examples are 'TemplateState' and 'PathwalkerState'.
    """
    def __init__(self, Analyzer):
        AnalyzerState.set_index(self, index.get())

        self.__analyzer               = Analyzer
        self.__door_id_replacement_db = None

    @property
    def engine_type(self):  return self.__analyzer.engine_type
    @property
    def init_state_f(self): return False
    @property
    def analyzer(self):     return self.__analyzer

    @property
    def door_id_replacement_db(self):
        """The MegaState implements a set of states. The entry doors of these
           states are now implemented in the MegaState_Entry. This property
           returns a dictionary that maps from doors of original states to
           doors of this MegaState which implement these doors.
        """
        if self.__door_id_replacement_db is None:
            result = {}
            for state_index in self.implemented_state_index_list():
                door_db = self.__analyzer.state_db[state_index].entry.door_db
                for transition_id, door_id in door_db.iteritems():
                    new_door_id     = self.entry.door_db.get(transition_id)
                    # The transition may have been deleted, for example, because
                    # it lies on the path of a uniform path walker.
                    if new_door_id is None: continue 
                    result[door_id] = new_door_id
            self.__door_id_replacement_db = result
        return self.__door_id_replacement_db

    def implemented_state_index_list(self):
        assert False, "This function needs to be overwritten by derived class."""

class MegaState_Target(object):
    """A mega state target contains the information about what the target
       state is inside an interval for a given template key. For example,
       a given interval X triggers to target scheme T, i.e. there is an
       element in the transition map:

                ...
                [ X, T ]
                ...

       then 'T.scheme[key]' tells the 'door id' of the door that is entered
       for the case the operates with the given 'key'. A key in turn, stands 
       for a particular state.

       There might be multiple intervals following the same target scheme,
       so the function 'TargetSchemeDB.get()' takes care of making 
       those schemes unique.

           .scheme = Target state index scheme as explained above.

           .index  = Unique index of the target scheme. This value is 
                     determined by 'TargetSchemeDB.get()'. It helps
                     later to define the scheme only once, even it appears
                     twice or more.
    """
    __slots__ = ('__index', '__scheme', '__drop_out_f', '__door_id', '__scheme')

    def __init__(self, Target, UniqueIndex=None):
        if UniqueIndex is not None: 
            assert isinstance(Target, tuple)
        else:
            assert    isinstance(Target, DoorID) \
                   or Target == E_StateIndices.DROP_OUT 

        self.__index       = UniqueIndex

        self.__drop_out_f  = False
        self.__door_id     = None
        self.__scheme      = None

        if   Target == E_StateIndices.DROP_OUT:  self.__drop_out_f  = True;   assert UniqueIndex is None
        elif isinstance(Target, DoorID):         self.__door_id     = Target; assert UniqueIndex is None
        elif isinstance(Target, tuple):          self.__scheme      = Target; assert UniqueIndex is not None

    @property
    def scheme(self):      return self.__scheme

    @property
    def door_id(self):     return self.__door_id

    def door_id_replacement(self, ReplacementDB):
        def replace_if_required(DoorId):
            replacement = ReplacementDB.get(DoorId)
            if replacement is not None: return replacement
            return DoorId

        if self.__door_id is not None:
            new_door_id = ReplacementDB.get(self.__door_id)
            if new_door_id is not None:
                self.__door_id = new_door_id
        else:
            self.__scheme = tuple(replace_if_required(door_id) for door_id in self.__scheme)

    @property
    def drop_out_f(self):  return self.__drop_out_f

    @property
    def index(self):       return self.__index

    def __repr__(self):
        if   self.drop_out_f:          return "MegaState_Target:DropOut"
        elif self.door_id is not None: return "MegaState_Target:(%s)" % repr(self.__door_id)
        elif self.scheme  is not None: return "MegaState_Target:scheme(%s)" % repr(self.__scheme)
        else:                          return "MegaState_Target:<ERROR>"

    def __hash__(self):
        return self.__index

    def __eq__(self, Other):
        if isinstance(Other, MegaState_Target) == False: return False
        ## if self.__index != Other.__index: return False
        return self.__scheme == Other.__scheme


