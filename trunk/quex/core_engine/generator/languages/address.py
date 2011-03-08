import quex.core_engine.state_machine.index         as index

def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "").replace("'", "")
    
db = {}

class AddressDB:
    #-----------------------------------------------------------------------
    #  Maps anything, such as a 'terminal' or anything else to an address.
    #  The address of a state machine state is the state's index. New
    #  addresses are generated using 'index.get()' which produces unique
    #  state indices.
    #-----------------------------------------------------------------------
    def __init__(self):
        self.__db = {}
        self.__special = set([
            "__RELOAD_FORWARD", "__RELOAD_BACKWARD", "__STATE_ROUTER", "__TERMINAL_ROUTER",
            "INIT_STATE_TRANSITION_BLOCK",
            "__REENTRY_PREPARATION", "__REENTRY",
        ])

    def get(self, NameOrTerminalID):
        """NameOrTerminalID is something that identifies a position/address 
                            in the code. This function returns a numeric id
                            for this address. 

           Exceptions are labels that are 'unique' inside a state machine 
           as defined by '__address_db_special'. For those the string itself
           is returned.
        """
        # Special addresses are not treated, but returned as string
        if NameOrTerminalID in self.__special:
            return NameOrTerminalID

        # If the thing is known, return its id immediately
        entry = self.__db.get(NameOrTerminalID)
        if entry != None: return entry

        # Generate unique id for the label: Use unique state index
        entry = index.get()
        self.__db[NameOrTerminalID] = entry
        return entry

__address_db = AddressDB()

__label_db = {
    # Let's make one thing clear: addresses of labels are aligned with state indices:
    "$entry":                 lambda StateIdx:   StateIdx,
    # 
    "$terminal":              lambda TerminalIdx: __address_db.get("TERMINAL_%s"        % __nice(TerminalIdx)),
    "$terminal-router":       lambda NoThing:     __address_db.get("__TERMINAL_ROUTER"),
    "$terminal-direct":       lambda TerminalIdx: __address_db.get("TERMINAL_%s_DIRECT" % __nice(TerminalIdx)),
    "$terminal-general-bw":   lambda NoThing:     __address_db.get("TERMINAL_GENERAL_BACKWARD"),
    "$terminal-EOF":          lambda NoThing:     __address_db.get("TERMINAL_END_OF_STREAM"),
    "$terminal-FAILURE":      lambda NoThing:     __address_db.get("TERMINAL_FAILURE"),
    #
    "$state-router":          lambda NoThing:     __address_db.get("__STATE_ROUTER"),
    #
    "$reload":                lambda StateIdx:    __address_db.get("STATE_%s_RELOAD"    % __nice(StateIdx)),
    "$reload-FORWARD":        lambda StateIdx:    __address_db.get("__RELOAD_FORWARD"),
    "$reload-BACKWARD":       lambda StateIdx:    __address_db.get("__RELOAD_BACKWARD"),
    #"$template":             lambda StateIdx:   "TEMPLATE_%s"       % __nice(StateIdx),
    #"$pathwalker":           lambda StateIdx:   "PATH_WALKER_%s"    % __nice(StateIdx),
    #"$pathwalker-router":    lambda StateIdx:   "PATH_WALKER_%s_STATE_ROUTER" % __nice(StateIdx),
    #"$entry-stub":           lambda StateIdx:   "STATE_%s_STUB"     % __nice(StateIdx),
    "$drop-out":              lambda StateIdx:    __address_db.get("STATE_%s_DROP_OUT_DIRECT" % __nice(StateIdx)),
    "$re-start":              lambda NoThing:     __address_db.get("__REENTRY_PREPARATION"),
    "$start":                 lambda NoThing:     __address_db.get("__REENTRY"),
    "$init_state_fw_transition_block": lambda NoThing: "INIT_STATE_TRANSITION_BLOCK",
}

def get_address(Type, Arg=None):
    """RETURNS A NUMBER that can be potentially be used for 
       routing (i.e. "switch( index ) { case N: goto _address; ... "
    """
    global __label_db
    result = __label_db[Type](Arg)

    assert type(result) in [int, long], \
           "Label type '%s' is not suited for routing." % Type
    return result

def get_label(LabelType, Arg=None):
    """RETURNS A STRING, that can be used directly for a goto statement."""
    global __label_db
    label_id = __label_db[LabelType](Arg)
    if type(label_id) in [int, long]: return get_label_of_address(label_id)
    else:                             return label_id

def get_label_of_address(Adr):
    """RETURNS A STRING--the label that belongs to a certain (numeric) address."""
    return "_%s" % __nice(Adr)

## 
__label_printed_list_unique               = set([])
__label_used_list_unique                  = set([])
__label_used_in_computed_goto_list_unique = set([])

def label_db_marker_init():
    global __label_printed_list_unique
    global __label_used_list_unique

    __label_printed_list_unique.clear()
    ## __label_printed_list_unique["__TERMINAL_ROUTER"] = True
    __label_used_list_unique.clear()

def label_db_register_usage(Label):
    __label_used_list_unique.add(Label)
    return Label

def label_db_unregister_usage(Label):
    __label_used_list_unique.remove(Label)

def label_db_get(Type, Index=None, GotoTargetF=False):
    assert type(Type)  in [str, unicode]
    assert Index == None or type(Index) in [int, long], \
           "Error: index '%s' for label type '%s'" % (repr(Index), Type)
    assert type(GotoTargetF) == bool
    global __label_printed_list_unique
    global __label_used_list_unique
    global __label_db

    label = __label_db[Type](Index)

    if Type in ["$re-start", "$start"]: return label

    # Keep track of any label. Labels which are not used as goto targets
    # may be deleted later on.
    if GotoTargetF: __label_used_list_unique.add(label)
    else:           __label_printed_list_unique.add(label)

    return label

def label_db_marker_get_unused_label_list():
    global __label_used_list_unique
    global __label_printed_list_unique
    global __label_db
    
    nothing_label_set       = []
    computed_goto_label_set = []

    printed       = __label_printed_list_unique
    used          = __label_used_list_unique
    computed_goto = __label_used_in_computed_goto_list_unique
    for label in printed:
        if label in used: continue
        if label in computed_goto:
            computed_goto_label_set.append(label)
        else:
            nothing_label_set.append(label)

    return nothing_label_set, computed_goto_label_set

class Address:
    def __init__(self, LabelType, LabelTypeArg, Code=None):
        """LabelType, LabelTypeArg --> used to access __address_db.

           Code  = Code that is to be generated, supposed that the 
                   label is actually referred.
                   (May be empty, so that that only the label is not printed.)
        """
        self.label = get_label(LabelType, LabelTypeArg)
        if   Code == None:       self.code = [ self.label, ":\n" ]
        elif type(Code) == list: self.code = Code
        else:                    self.code = [ Code ]

class Reference:
    def __init__(self, LabelType, LabelTypeArg=None, Code=None, RoutingF=False):
        """LabelType, LabelTypeArg --> used to access __address_db.
           
           Code  = Code fragment that references the label.

           RoutingF = The existence of this reference requires a mentioning 
                      in the state router table.
        """
        self.label = get_label(LabelType, LabelTypeArg)
        if    Code == None:      self.code = [ self.label ]
        elif type(Code) == list: self.code = Code 
        else:                    self.code = [ Code ]

        self.routing_f = RoutingF
        if RoutingF: self.address = get_address(LabelType, LabelTypeArg)
        else:        self.address = None

_referenced_label_set = set([])

def get_plain_strings(txt_list, RoutingInfoF=True):
    global _referenced_label_set

    _referenced_label_set.clear()

    while 1 + 1 == 2:
        prev_size = len(_referenced_label_set)
        _resolve_references(txt_list)
        # If no new references where found, then finalize the text
        if prev_size == len(_referenced_label_set): break

        # Fill in code fragments that have been referenced
        _fill_text(txt_list)

    # Delete unreferenced code fragments.
    # Replace integers by indentations
    print "##", _referenced_label_set
    return _finalize_text(txt_list)

def _resolve_references(txt_list):
    global _referenced_label_set

    for i, elm in enumerate(txt_list):
        if isinstance(elm, Reference):
            _referenced_label_set.add(elm.label)
            # A reference has done its work as soon as it has notified about
            # its existence. Now, its code can replace its position.
            if len(elm.code) == 1: txt_list[i] = elm.code[0]
            else:                  txt_list    = txt_list[:i] + elm.code + txt_list[i+1:]

        elif isinstance(elm, Address):
            # An 'addressed' code fragment may contain further references.
            _resolve_references(elm.code)
        
def _fill_text(txt_list):
    """If an addressed code fragment is referenced, then it is inserted.
    """
    global _referenced_label_set

    for i, elm in enumerate(txt_list):
        if not isinstance(elm, Address): continue
        if elm.label in _referenced_label_set: 
            if len(elm.code) == 1: txt_list[i] = elm.code[0]
            else:                  txt_list    = txt_list[:i] + elm.code + txt_list[i+1:]

    return txt_list

def _finalize_text(txt_list):
    """-- Replaces unreferenced 'Address' objects by empty strings.
       -- Replaces integers by indentation, i.e. '1' = 4 spaces.
    """
    for i, elm in enumerate(txt_list):
        if isinstance(elm, Address):
            if elm.label in _referenced_label_set: txt_list[i] = "".join(elm.code)
            else:                                  txt_list[i] = ""; print "##not:", elm.label
        elif type(elm) in [int, long]:    # Indentation: elm = number of indentations
            txt_list[i] = "    " * elm

    return txt_list

def find_routed_address_set(txt_list):
    result = set([])
    for i, elm in enumerate(txt_list):
        if isinstance(elm, Reference) and elm.routing_f: result.add(elm.address)
    return result
