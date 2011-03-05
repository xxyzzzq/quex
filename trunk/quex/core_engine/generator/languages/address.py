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
    "$entry":                 lambda StateIdx:   "_%s"               % __nice(StateIdx),
    #"$entry-stub":           lambda StateIdx:   "STATE_%s_STUB"     % __nice(StateIdx),
    "$drop-out-direct":       lambda StateIdx:    __address_db.get("STATE_%s_DROP_OUT_DIRECT" % __nice(StateIdx)),
    "$re-start":              lambda NoThing:     __address_db.get("__REENTRY_PREPARATION"),
    "$start":                 lambda NoThing:     __address_db.get("__REENTRY"),
    "$init_state_fw_transition_block": lambda NoThing: "INIT_STATE_TRANSITION_BLOCK",
}

def get_address(Type, Index=None):
    global __label_db
    return __label_db[Type](Index)

def get_label(LabelType, Index=None):
    global __label_db
    return _pure_position(__label_db[LabelType](Index))

def _pure_position(LabelID):
    if type(LabelID) in [int, long]: return "_%s" % __nice(LabelID)
    else:                            return LabelID

def _position(NameOrTerminalID):
    return _pure_position(__address_db.get(NameOrTerminalID))

#__label_db = \
#{
#    "$terminal":              lambda TerminalIdx: _position("TERMINAL_%s"        % __nice(TerminalIdx)),
#    "$terminal-router":       lambda NoThing:     _position("__TERMINAL_ROUTER"),
#    "$state-router":          lambda NoThing:     _position("__STATE_ROUTER"),
#    "$terminal-direct":       lambda TerminalIdx: _position("TERMINAL_%s_DIRECT" % __nice(TerminalIdx)),
#    "$terminal-general-bw":   lambda NoThing:     _position("TERMINAL_GENERAL_BACKWARD"),
#    "$terminal-EOF":          lambda NoThing:     _position("TERMINAL_END_OF_STREAM"),
#    "$terminal-FAILURE":      lambda NoThing:     _position("TERMINAL_FAILURE"),
#    "$template":              lambda StateIdx:    "TEMPLATE_%s"       % __nice(StateIdx),
#    "$pathwalker":            lambda StateIdx:    "PATH_WALKER_%s"    % __nice(StateIdx),
#    "$pathwalker-router":     lambda StateIdx:    "PATH_WALKER_%s_STATE_ROUTER" % __nice(StateIdx),
#    "$entry":                 lambda StateIdx:    "_%s"               % __nice(StateIdx),
#    "$entry-stub":            lambda StateIdx:    "STATE_%s_STUB"     % __nice(StateIdx),
#    "$reload":                lambda StateIdx:    _position("STATE_%s_RELOAD"          % __nice(StateIdx)),
#    "$reload-FORWARD":        lambda StateIdx:    _position("__RELOAD_FORWARD"),
#    "$reload-BACKWARD":       lambda StateIdx:    _position("__RELOAD_BACKWARD"),
#    "$drop-out-direct":       lambda StateIdx:    _position("STATE_%s_DROP_OUT_DIRECT" % __nice(StateIdx)),
#    "$re-start":              lambda NoThing:     "__REENTRY_PREPARATION",
#    "$start":                 lambda NoThing:     "__REENTRY",
#    "$init_state_fw_transition_block": lambda NoThing: "INIT_STATE_TRANSITION_BLOCK",
#}

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
    def __init__(self, Type, Arg, Code=""):
        """Label = label under which the code is addressed.
           Code  = Code that is to be generated, supposed that the 
                   label is actually referred.
                   (May be empty, so that that only the label is not printed.)
        """
        self.label = get_address(Type, Arg)
        self.code = [ _pure_position(self.label), ":\n" ]
        if type(Code) == list: self.code.extend(Code)
        else:                  self.code.append(Code)

class Reference:
    def __init__(self, Type, Arg=None):
        """Label = label that is referenced in 'Code'.
           Code  = Code fragment that references the label.
        """
        if Type == "$goto":
            self.label = Arg
            self.code  = "goto %s;\n" % _pure_position(self.label)

        elif Type == "$reference":
            self.label = Arg
            self.code  = "QUEX_LABEL(%s)" % self.label

        elif Type == "$set-last_acceptance":
            self.label = get_address("$terminal-direct", Arg)
            self.code  = "last_acceptance                = QUEX_LABEL(%s);\n" % self.label

        elif Type == "$goto-last_acceptance":
            self.label = "__TERMINAL_ROUTER"
            self.code  = Arg["$goto-last_acceptance"]

        elif Type == "$address":
            self.label = Arg
            self.code = _pure_position(self.label)

        self.reference_type = Type

    def __repr__(self):
        return self.code
