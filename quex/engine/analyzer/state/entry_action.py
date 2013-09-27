from   quex.engine.analyzer.commands import CommandList

from   quex.blackboard import setup as Setup, \
                              E_StateIndices, \
                              E_PreContextIDs, \
                              E_TriggerIDs, \
                              E_AcceptanceIDs, \
                              E_DoorIdIndex

from   collections     import namedtuple

class DoorID(namedtuple("DoorID_tuple", ("state_index", "door_index"))):
    def __new__(self, StateIndex, DoorIndex):
        assert isinstance(StateIndex, (int, long)) or StateIndex in E_StateIndices or StateIndex == E_AcceptanceIDs.FAILURE
        # 'DoorIndex is None' --> right after the entry commands (targetted after reload).
        assert isinstance(DoorIndex, (int, long))  or DoorIndex is None or DoorIndex in E_DoorIdIndex, "%s" % DoorIndex
        return super(DoorID, self).__new__(self, StateIndex, DoorIndex)

    @staticmethod
    def drop_out(StateIndex):             return DoorID(StateIndex, E_DoorIdIndex.DROP_OUT)
    @staticmethod                        
    def transition_block(StateIndex):     return DoorID(StateIndex, E_DoorIdIndex.TRANSITION_BLOCK)
    @staticmethod                        
    def global_state_router():            return DoorID(0,          E_DoorIdIndex.GLOBAL_STATE_ROUTER)
    @staticmethod                        
    def acceptance(PatternId):                                return DoorID(PatternId,  E_DoorIdIndex.ACCEPTANCE)
    @staticmethod                        
    def state_machine_entry(SM_Id):                           return DoorID(SM_Id,      E_DoorIdIndex.STATE_MACHINE_ENTRY)
    @staticmethod                        
    def backward_input_position_detector_return(PatternId):   return DoorID(PatternId,  E_DoorIdIndex.BIPD_RETURN)
    @staticmethod                         
    def global_end_of_pre_context_check(): return DoorID(0, E_DoorIdIndex.GLOBAL_END_OF_PRE_CONTEXT_CHECK)
    @staticmethod                        
    def global_terminal_end_of_file():     return DoorID(0, E_DoorIdIndex.GLOBAL_TERMINAL_END_OF_FILE)
    @staticmethod
    def global_reentry():                  return DoorID(0, E_DoorIdIndex.GLOBAL_REENTRY)
    @staticmethod
    def global_reentry_preparation():      return DoorID(0, E_DoorIdIndex.GLOBAL_REENTRY_PREPARATION)
    @staticmethod
    def global_reentry_preparation_2():    return DoorID(0, E_DoorIdIndex.GLOBAL_REENTRY_PREPARATION_2)

    def drop_out_f(self):                  return self.door_index == E_DoorIdIndex.DROP_OUT

    def __repr__(self):
        return "DoorID(s=%s, d=%s)" % (self.state_index, self.door_index)

class DoorID_Scheme(tuple):
    """A TargetByStateKey maps from a index, i.e. a state_key to a particular
       target (e.g. a DoorID). It is implemented as a tuple which can be 
       identified by the class 'TargetByStateKey'.
    """
    def __new__(self, DoorID_List):
        return tuple.__new__(self, DoorID_List)

    @staticmethod
    def concatinate(This, That):
        door_id_list = list(This)
        door_id_list.extend(list(That))
        return DoorID_Scheme(door_id_list)

class TransitionID(namedtuple("TransitionID_tuple", ("target_state_index", "source_state_index", "trigger_id"))):
    """Objects of this type identify a transition. 
    
                   .----- trigger_id ---->-[ TransitionAction ]----.
                   |                                               |
        .--------------------.                          .--------------------.
        | source_state_index |                          | target_state_index |
        '--------------------'                          '--------------------'
    
       NOTE: There might be multiple transitions from source to target. Each transition
             has another trigger_id. The relation between a TransitionID and a 
             TransitionAction is 1:1.

    """
    def __new__(self, StateIndex, FromStateIndex, TriggerId):
        assert isinstance(StateIndex, (int, long))     or StateIndex     in E_StateIndices
        assert isinstance(FromStateIndex, (int, long)) or FromStateIndex in E_StateIndices
        assert isinstance(TriggerId, (int, long))      or TriggerId      in E_TriggerIDs
        return super(TransitionID, self).__new__(self, StateIndex, FromStateIndex, TriggerId)

    def is_from_reload(self):
        return   self.source_state_index == E_StateIndices.RELOAD_FORWARD \
              or self.source_state_index == E_StateIndices.RELOAD_BACKWARD

    def __repr__(self):
        source_state_str = "%s" % self.source_state_index

        if self.trigger_id == 0:
            return "TransitionID(to=%s, from=%s)" % (self.target_state_index, source_state_str)
        else:
            return "TransitionID(to=%s, from=%s, trid=%s)" % (self.target_state_index, source_state_str, self.gtrigger_id)

class TransitionAction(object):
    """Object containing information about commands to be executed upon
       transition into a state.

       .command_list  --> list of commands to be executed upon the transition.
       .door_id       --> An 'id' which is supposed to be unique for a command list. 
                          It is (re-)assigned during the process of 
                          'EntryActionDB.categorize()'.
    """
    __slots__ = ("door_id", "_command_list")
    def __init__(self, CommandListObjectF=True):
        # NOTE: 'DoorId' is not accepted as argument. Is needs to be assigned
        #       by '.categorize()' in the action_db. Then, transition actions
        #       with the same CommandList-s share the same DoorID.
        assert type(CommandListObjectF) == bool
        self.door_id = None # DoorID into door tree from where the command list is executed
        if CommandListObjectF: self._command_list = CommandList() 
        else:                  self.command_list = None
 
    @property
    def command_list(self): 
        return self._command_list

    @command_list.setter
    def command_list(self, CL): 
        assert isinstance(CL, CommandList) or CL is None
        self._command_list = CL
        
    def clone(self):
        result = TransitionAction(CommandListObjectF=False)
        result.door_id       = self.door_id  # DoorID-s are immutable
        result._command_list = self._command_list.clone()
        return result

    # Make TransitionAction usable for dictionary and set
    def __hash__(self):      
        return hash(self._command_list)

    def __eq__(self, Other):
        return self._command_list == Other._command_list

    def __repr__(self):
        return "(%s: [%s])" % (self.door_id, self._command_list)

