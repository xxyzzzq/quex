import quex.engine.state_machine.index         as     index
from   quex.engine.analyzer.state.entry_action import DoorID
from   quex.engine.tools                       import print_callstack, TypedDict
from   quex.blackboard import E_AcceptanceIDs
#______________________________________________________________________________
#
# DoorID:
#
# Marks an entrance into a 'Processor', an AnalyzerState for example.  A
# Processor can have multiple entries, each entry has a different DoorID. A
# DoorID identifies distinctly a CommandList to be executed upon entry.
# No two CommandList-s
# are the same except that their DoorID is the same.
#            
#______________________________________________________________________________
#
# Label:
#
# Identifier in the generated source code which can be 'gotoed'. A label is
# distinctly linked with a DoorID and an Address, i.e.
#______________________________________________________________________________
#
# Address:
#
# Numeric representation of a label. Using an address a variable may contain
# the information of what label to go, and the goto is then executed by a
# code fragment as
#
#      switch( address_variable ) {
#         ...
#         case 0x4711:  goto _4711;
#         ...
#      }
#______________________________________________________________________________
#
# TransitionID:
#
# Identifies a transition from one source to target state.  There may be
# multiple transitions for the same source-target pair. Each one identified by
# an additional 'trigger_id'.  TransitionIDs are connected with CommandList-s
# at entry into a state; But 
#
#                               n          1
#               TransitionID  <--------------> CommandList
#
# That is, there may be multiple TransitionID-s with the same CommandList.
# TransitionID-s are useful during the construction of entries.
#______________________________________________________________________________



#______________________________________________________________________________
# DialDB: DoorID, Address, Label - Database
#
# For a given Label, a given Address, or a given DoorID, there the remaining
# two a distinctly defined. That is,
#
#                           1     n         
#               StateIndex <-------> DoorID 
#                                   1 /   \ 1
#                                    /     \
#                                   /       \
#                                1 /         \ 1
#                           Address <-------> Label
#                                    1     1
# 
# The DialDB maintains the injective relationships and finds equivalents
# for one given element. All addresses/labels/door-ids relate to a state
# with a given StateIndex. 
#______________________________________________________________________________
class DialDB:
    __slots__ = ( "__d2la", "__door_id_db", "__gotoed_address_set", "__routed_address_set" )
    def __init__(self):
        # Database: [DoorID] [Address] [Label] 
        # 
        # The database is represented by a dictionary that maps:
        #
        #               DoorID --> tuple(Label, Address)
        #
        self.__d2la = {}  

        # Track all generated DoorID objects with 2d-dictionary that maps:
        #
        #          StateIndex --> ( DoorSubIndex --> DoorID )
        #
        # Where the DoorID has the 'state_index' and 'door_index' equal to
        # 'StateIndex' and 'DoorSubIndex'.
        #
        self.__door_id_db = {}  
       
        # Track addresses which are subject to 'goto' and those which need to
        # be routed.
        self.__gotoed_address_set = TypedSet(long)
        self.__routed_address_set = TypedSet(long)

   def clear(self):
       self.__d2la.clear()
       self.__door_id_db.clear()
       self.__gotoed_address_set.clear()
       self.__routed_address_set.clear()

    def routed_address_set(self):
        return self.__routed_address_set

    def gotoed_address_set(self):
        return self.__gotoed_address_set

    def label_is_gotoed(self, Label):
        address = self.get_address_by_label(Label)
        return address in self.__gotoed_address_set

    def __new_entry(self, StateIndex=None, DoorSubIndex=None, Label=None):
        if StateIndex is None:   state_index = index.get() # generate a new StateIndex
        else:                    state_index = StateIndex
        if DoorSubIndex is None: door_sub_index = self.generate_door_sub_index(state_index) 
        else:                    door_sub_index = DoorSubIndex

        door_id = self.access_door_id(state_index, door_sub_index)  
        address = self.generate_address() 
        if Label is None: label = self.label_from_address(address)
        else:             label = Label
        self.enter(door_id, address, label)
        return door_id, address, label

    def access_door_id(self, StateIndex, DoorSubIndex):
        """Try to get a DoorID from the set of existing DoorID-s. If a DoorID
        with 'StateIndex' and 'DoorSubIndex' does not exist yet, then create it.
        """
        sub_db = self.__door_id_db.get(StateIndex)
        if sub_db is None:
            door_id, address, label = self.__new_entry(StateIndex, DoorSubIndex)
            self.__door_id_db[StateIndex] = { DoorSubIndex: door_id }
            return door_id

        result = sub_db.get(DoorSubIndex)
        if result is None:
            door_id, address, label = self.__new_entry(StateIndex, DoorSubIndex)
            sub_db[DoorSubIndex] = door_id
        return door_id

    def new_door_id(self, StateIndex=None):
        door_id, address, label = self.__new_entry(StateIndex)
        return door_id

    def new_address(self, StateIndex=None):
        door_id, address, label = self.__new_entry(StateIndex)
        return address

    def new_label(self, StateIndex=None):
        door_id, address, label = self.__new_entry(StateIndex)
        return label

    def get_label_by_door_id(self, DoorId, GotoedF=False):
        assert DoorId in self.__d2la
        if GotoedF:
            address, label = self.__d2la(DoorId) 
            self.__gotoed_address_set.add(address)
            return label
        else:
            return self.__d2la[DoorId][1]

    def get_address_by_door_id(self, DoorId, RoutedF=False):
        address = self.__d2la[DoorId][0]
        if RoutedF:
            self.mark_address_as_routed(address)
        return address

    def get_door_id_by_address(self, Address):
        for door_id, info in self.__d2la.iteritems():
            if info[0] == Address: return door_id
        return None

    def get_label_by_address(self, Address):
        for door_id, info in self.__d2la.iteritems():
            if info[0] == Address: return info[1]
        return None

    def get_door_id_by_label(self, Label):
        for door_id, info in self.__d2la.iteritems():
            if info[1] == Label: return door_id
        return None

    def get_address_by_label(self, Label):
        for door_id, info in self.__d2la.iteritems():
            if info[1] == Label: return info[0]
        return None

    def mark_address_as_gotoed(self, Address):
        self.__gotoed_address_set.add(Address)

    def mark_label_as_gotoed(self, Label):
        self.mark_address_as_gotoed(self.get_address_by_label(Label))

    def mark_door_id_as_gotoed(self, DoorId):
        self.mark_address_as_gotoed(self.get_address_by_door_id(DoorId))

    def mark_address_as_routed(self, Address):
        self.__routed_address_set.add(Address)
        # Any address which is subject to routing is 'gotoed', at least inside
        # the router (e.g. "switch( ... ) ... case AdrX: goto LabelX; ...").
        self.__gotoed_address_set.add(Address)

    def mark_label_as_routed(self, Label):
        self.mark_address_as_routed(self.get_address_by_label(Label))

    def mark_door_id_as_routed(self, DoorId):
        self.mark_address_as_routed(self.get_address_by_door_id(DoorId))

    def label_from_address(Adr):
        #if Adr in special_label_db:
        #    return special_label_db[Adr]
        return "_%s" % Adr


dial_db = DialDB()

class DoorID(namedtuple("DoorID_tuple", ("state_index", "door_index"))):
    def __new__(self, StateIndex, DoorIndex):
        assert isinstance(StateIndex, (int, long)) or StateIndex in E_StateIndices or StateIndex == E_AcceptanceIDs.FAILURE
        # 'DoorIndex is None' --> right after the entry commands (targetted after reload).
        assert isinstance(DoorIndex, (int, long))  or DoorIndex is None or DoorIndex in E_DoorIdIndex, "%s" % DoorIndex
        return super(DoorID, self).__new__(self, StateIndex, DoorIndex)

    @staticmethod
    def drop_out(StateIndex):              return dial_db.access_door_id(StateIndex, E_DoorIdIndex.DROP_OUT)
    @staticmethod                        
    def transition_block(StateIndex):      return dial_db.access_door_id(StateIndex, E_DoorIdIndex.TRANSITION_BLOCK)
    @staticmethod                        
    def global_state_router():             return dial_db.access_door_id(0,          E_DoorIdIndex.GLOBAL_STATE_ROUTER)
    @staticmethod                        
    def acceptance(PatternId):             return dial_db.access_door_id(PatternId,  E_DoorIdIndex.ACCEPTANCE)
    @staticmethod                        
    def state_machine_entry(SM_Id):        return dial_db.access_door_id(SM_Id,      E_DoorIdIndex.STATE_MACHINE_ENTRY)
    @staticmethod                         
    def global_end_of_pre_context_check(): return dial_db.access_door_id(0, E_DoorIdIndex.GLOBAL_END_OF_PRE_CONTEXT_CHECK)
    @staticmethod                        
    def global_terminal_end_of_file():     return dial_db.access_door_id(0, E_DoorIdIndex.GLOBAL_TERMINAL_END_OF_FILE)
    @staticmethod
    def global_reentry():                  return dial_db.access_door_id(0, E_DoorIdIndex.GLOBAL_REENTRY)
    @staticmethod
    def global_reentry_preparation():      return dial_db.access_door_id(0, E_DoorIdIndex.GLOBAL_REENTRY_PREPARATION)
    @staticmethod
    def global_reentry_preparation_2():    return dial_db.access_door_id(0, E_DoorIdIndex.GLOBAL_REENTRY_PREPARATION_2)

    def drop_out_f(self):                  return self.door_index == E_DoorIdIndex.DROP_OUT

    def __repr__(self):
        return "DoorID(s=%s, d=%s)" % (self.state_index, self.door_index)

class Label:
    """This class shall be a short-hand for 'get_label_by_door_id' of global
       labels. It was designed to provide the same interface as the 'DoorID.global_*' 
       functions.
    """
    @staticmethod
    def drop_out(StateIndex, GotoedF=False):         return dial_db.get_label_by_door_id(DoorID.drop_out(StateIndex), GotoedF)
    @staticmethod                        
    def transition_block(StateIndex, GotoedF=False): return dial_db.get_label_by_door_id(DoorID.transition_block(StateIndex), GotoedF)
    @staticmethod
    def global_state_router(GotoedF=False):          return dial_db.get_label_by_door_id(DoorID.global_state_router(), GotoedF)
    @staticmethod
    def global_terminal_end_of_file(GotoedF=False):  return dial_db.get_label_by_door_id(DoorID.global_terminal_end_of_file(), GotoedF)
    @staticmethod
    def acceptance(PatternId, GotoedF=False):        return dial_db.get_label_by_door_id(DoorID.acceptance(PatternId), GotoedF)
    @staticmethod                        
    def state_machine_entry(SM_Id, GotoedF=False):   return dial_db.get_label_by_door_id(DoorID.state_machine_entry(SM_Id), GotoedF)
    @staticmethod
    def global_reentry(GotoedF=False):               return dial_db.get_label_by_door_id(DoorID.global_reentry(), GotoedF)
    @staticmethod
    def global_reentry_preparation(GotoedF=False):   return dial_db.get_label_by_door_id(DoorID.global_reentry_preparation(), GotoedF)
    @staticmethod
    def global_reentry_preparation_2(GotoedF=False): return dial_db.get_label_by_door_id(DoorID.global_reentry_preparation_2(), GotoedF)

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


__routed_address_set = set([])

class IfDoorIdReferencedCode:
    def __init__(self, DoorId, Code=None):
        """LabelType, LabelTypeArg --> used to access __address_db.

           Code  = Code that is to be generated, supposed that the 
                   label is actually referred.
                   (May be empty, so that that only the label is not printed.)
        """
        assert isinstance(Code, list) or Code is None

        self.label = dial_db.map_door_id_to_label(DoorId)
        if Code is None: self.code = [ self.label, ":" ]
        else:            self.code = Code

class IfDoorIdReferencedLabel(IfDoorIdReferencedCode):
    def __init__(self, DoorId):
        IfDoorIdReferencedCode.__init__(self, DoorId)

def get_plain_strings(txt_list, RoutingInfoF=True):
    """-- Replaces unreferenced 'CodeIfLabelReferenced' objects by empty strings.
       -- Replaces integers by indentation, i.e. '1' = 4 spaces.
    """

    size = len(txt_list)
    i    = -1
    while i < size - 1:
        i += 1

        elm = txt_list[i]

        if type(elm) in [int, long]:    
            # Indentation: elm = number of indentations
            txt_list[i] = "    " * elm

        elif not isinstance(elm, IfDoorIdReferencedCode): 
            # Text is left as it is
            continue

        elif dial_db.label_is_gotoed(elm.label): 
            # If an address is referenced, the correspondent code is inserted.
            txt_list[i:i+1] = elm.code
            # txt_list = txt_list[:i] + elm.code + txt_list[i+1:]
            size += len(elm.code) - 1
            i    -= 1
        else:
            # If an address is not referenced, the it is replaced by an empty string
            txt_list[i] = ""

    return txt_list

def __nice(SM_ID): 
    assert isinstance(SM_ID, (long, int))
    return repr(SM_ID).replace("L", "").replace("'", "")
    
#__label_db = {
#    # Let's make one thing clear: addresses of labels are aligned with state indices:
#    "$entry":                 lambda DoorId:      __address_db.get_entry(DoorId),
#    # 
#    "$terminal":              lambda TerminalIdx: __address_db.get("TERMINAL_%s"        % __nice(TerminalIdx)),
#    "$terminal-router":       lambda NoThing:     __address_db.get("__TERMINAL_ROUTER"),
#    "$terminal-direct":       lambda TerminalIdx: __address_db.get("TERMINAL_%s_DIRECT" % __nice(TerminalIdx)),
#    "$terminal-general-bw":   lambda NoThing:     __address_db.get("TERMINAL_GENERAL_BACKWARD"),
#    "$terminal-EOF":          lambda NoThing:     __address_db.get("TERMINAL_END_OF_STREAM"),
#    "$terminal-FAILURE":      lambda SM_Id:       __address_db.get("TERMINAL_FAILURE_%s" % SM_Id),
#    #
#    "$state-router":          lambda NoThing:     __address_db.get("__STATE_ROUTER"),
#    #
#    "$reload":                lambda StateIdx:    __address_db.get("STATE_%s_RELOAD"    % __nice(StateIdx)),
#    "$reload-FORWARD":        lambda StateIdx:    __address_db.get("__RELOAD_FORWARD"),
#    "$reload-BACKWARD":       lambda StateIdx:    __address_db.get("__RELOAD_BACKWARD"),
#    "$drop-out":              lambda StateIdx:    __address_db.get("STATE_%s_DROP_OUT" % __nice(StateIdx)),
#    "$re-start":              lambda NoThing:     __address_db.get("__REENTRY_PREPARATION"),
#    "$re-start-2":            lambda NoThing:     __address_db.get("__REENTRY_PREPARATION_2"),
#    "$start":                 lambda NoThing:     __address_db.get("__REENTRY"),
#    "$skipper-reload":        lambda StateIdx:    __address_db.get("__SKIPPER_RELOAD_TERMINATED_%s" % __nice(StateIdx)),
#    "$bipd-return":           lambda DetectorID:  __address_db.get("BIPD_%i_RETURN" % DetectorID),
#    "$bipd-terminal":         lambda DetectorID:  __address_db.get("BIPD_%i_TERMINAL" % DetectorID),
#    # There may be more than one ... in skipp for example ...
#    "$init_state_transition_block": lambda StateIndex:   __address_db.get("INIT_STATE_%i_TRANSITION_BLOCK" % StateIndex),
#}
