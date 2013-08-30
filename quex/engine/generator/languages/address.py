import quex.engine.state_machine.index         as index
from   quex.engine.analyzer.state.entry_action import DoorID
from   quex.engine.tools import print_callstack, TypedDict

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
special_labels = (
    (DoorID.global_reload_forward(),              "RELOAD_FORWARD"),
    (DoorID.global_reload_backward(),             "RELOAD_BACKWARD"),
    (DoorID.global_state_router(),                "STATE_ROUTER"),
    (DoorID.global_terminal_router(),             "TERMINAL_ROUTER"),
    (DoorID.global_terminal_end_of_file(),        "TERMINAL_END_OF_FILE"),
    (DoorID.global_terminal_failure(),            "TERMINAL_FAILURE"),
    (DoorID.global_reentry(),                     "REENTRY"),
    (DoorID.global_reentry_preparation(),         "REENTRY_PREPARATION"),
    (DoorID.global_reentry_preparation_2(),       "REENTRY_PREPARATION_2"),
)

__door_id_to_address_db = TypedDict(DoorID, long)

def map_door_id_to_address(DoorId):
    """RETURNS: Address of given DoorId

       Ensures that there is an entry in __door_id_to_address_db for
       the given DoorId.
    """
    global __door_id_to_address_db
    address = __door_id_to_address_db.get(DoorId)
    if address is None:
        address = index.get()
        __door_id_to_address_db[DoorId] = address
    return address

special_label_db = dict(
    (map_door_id_to_address(door_id), label)
    for door_id, label in special_labels
)

def map_address_to_label(Adr):
    if Adr in special_label_db:
        special_label_db[Adr]
    return "_%s" % Adr

def map_door_id_to_label(DoorId, GotoedF=False):
    # 'map_door_id_to_address' ensures that there is an address for the DoorId
    #
    label = map_address_to_label(map_door_id_to_address(DoorId))
    if GotoedF: mark_label_as_gotoed(GotoedF)
    return label

def get_new_address():
    state_index = index.get()
    return map_door_id_to_address(DoorID(state_index, 0))

class Label:
    """This class shall be a short-hand for 'map_door_id_to_address' of global
       labels. It was designed to provide the same interface as the 'DoorID.global_*' 
       functions.
    """
    @staticmethod
    def drop_out(StateIndex, GotoedF=False):         return map_door_id_to_label(DoorID.drop_out(StateIndex), GotoedF)
    @staticmethod                        
    def goto_reload(GotoedF=False):                  return map_door_id_to_label(DoorID.goto_reload(StateIndex), GotoedF)
    @staticmethod                        
    def after_reload(StateIndex, GotoedF=False):     return map_door_id_to_label(DoorID.after_reload(StateIndex), GotoedF)
    @staticmethod                        
    def transition_block(StateIndex, GotoedF=False): return map_door_id_to_label(DoorID.transition_block(StateIndex), GotoedF)
    @staticmethod
    def global_reload_forward(GotoedF=False):        return map_door_id_to_label(DoorID.global_reload_forward(), GotoedF)
    @staticmethod
    def global_reload_backward(GotoedF=False):       return map_door_id_to_label(DoorID.global_reload_backward(), GotoedF)
    @staticmethod
    def global_state_router(GotoedF=False):          return map_door_id_to_label(DoorID.global_state_router(), GotoedF)
    @staticmethod
    def global_terminal_router(GotoedF=False):       return map_door_id_to_label(DoorID.global_terminal_router(), GotoedF)
    @staticmethod
    def global_terminal_end_of_file(GotoedF=False):  return map_door_id_to_label(DoorID.global_terminal_end_of_file(), GotoedF)
    @staticmethod
    def acceptance(PatternId, GotoedF=False):        return map_door_id_to_label(DoorID.acceptance(PatternId), GotoedF)
    @staticmethod
    def global_terminal_failure(GotoedF=False):      return map_door_id_to_label(DoorID.global_terminal_failure(), GotoedF)
    @staticmethod
    def global_reentry(GotoedF=False):               return map_door_id_to_label(DoorID.global_reentry(), GotoedF)
    @staticmethod
    def global_reentry_preparation(GotoedF=False):   return map_door_id_to_label(DoorID.global_reentry_preparation(), GotoedF)
    @staticmethod
    def global_reentry_preparation_2(GotoedF=False): return map_door_id_to_label(DoorID.global_reentry_preparation_2(), GotoedF)

__referenced_label_set     = set([])
__state_router_address_set = set([])

def mark_label_as_gotoed(Label):
    __referenced_label_set.add(Label)

def mark_door_id_as_gotoed(DoorId):
    mark_label_as_gotoed(map_door_id_to_label(DoorId))

def mark_address_for_state_routing(Adr):
    __state_router_address_set.add(Adr)
    # Any address which is subject to state routing relates to a label which
    # is 'gotoed' from inside the state router.
    mark_label_as_gotoed(map_address_to_label(Adr))

def address_exists(Address):
    global __referenced_label_set
    return get_label_of_address(Address) in __referenced_label_set

def init_address_handling():
    __referenced_label_set.clear()
    __state_router_address_set.clear()

def get_address_set_subject_to_routing():
    return __state_router_address_set

class CodeIfDoorIdReferenced:
    def __init__(self, DoorId, Code=None):
        """LabelType, LabelTypeArg --> used to access __address_db.

           Code  = Code that is to be generated, supposed that the 
                   label is actually referred.
                   (May be empty, so that that only the label is not printed.)
        """
        assert isinstance(Code, list) or Code is None

        self.label = map_door_id_to_label(DoorId)
        if Code is None: self.code = [ self.label, ":\n" ]
        else:            self.code = Code

class LabelIfDoorIdReferenced(CodeIfDoorIdReferenced):
    def __init__(self, DoorId):
        CodeIfDoorIdReferenced.__init__(self, DoorId)

def get_plain_strings(txt_list, RoutingInfoF=True):
    """-- Replaces unreferenced 'CodeIfLabelReferenced' objects by empty strings.
       -- Replaces integers by indentation, i.e. '1' = 4 spaces.
    """
    global __referenced_label_set

    size = len(txt_list)
    i    = -1
    while i < size - 1:
        i += 1

        elm = txt_list[i]

        if type(elm) in [int, long]:    
            # Indentation: elm = number of indentations
            txt_list[i] = "    " * elm

        elif not isinstance(elm, CodeIfDoorIdReferenced): 
            # Text is left as it is
            continue

        elif elm.label in __referenced_label_set: 
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
    
