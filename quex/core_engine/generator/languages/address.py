import quex.core_engine.state_machine.index         as index

def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "").replace("'", "")
    
db = {}

#-----------------------------------------------------------------------------------------
# terminal_state_index_db: Maps from a terminal index to a state index.
#-----------------------------------------------------------------------------------------
__terminal_state_index_db = { }

def map_label_to_state_index(NameOrTerminalID):
    """Assigns a unique state index to a terminal id. A terminal id either
       corresponds to a state index or 'END_OF_STREAM', or 'FAILURE'.
    """
    global __terminal_state_index_db

    # if type(NameOrTerminalID) not in [int, long]:
    #    assert NameOrTerminalID in ["END_OF_STREAM", "FAILURE", "GENERAL_BACKWARD"] \
    #           or NameOrTerminalID.find("_DIRECT")

    entry = __terminal_state_index_db.get(NameOrTerminalID)
    ## print "##in: ", NameOrTerminalID, "\t", entry
    if entry != None: return entry

    entry = index.get()
    __terminal_state_index_db[NameOrTerminalID] = entry
    ## print "##out:", NameOrTerminalID, "\t", entry
    return entry

def get_address(Type, Index=None):
    return {
        "$terminal":              lambda TerminalIdx: map_label_to_state_index("TERMINAL_%s"        % __nice(TerminalIdx)),
        "$terminal-direct":       lambda TerminalIdx: map_label_to_state_index("TERMINAL_%s_DIRECT" % __nice(TerminalIdx)),
        "$terminal-general-bw":   lambda NoThing:     map_label_to_state_index("TERMINAL_GENERAL_BACKWARD"),
        "$terminal-EOF":          lambda NoThing:     map_label_to_state_index("TERMINAL_END_OF_STREAM"),
        "$terminal-FAILURE":      lambda NoThing:     map_label_to_state_index("TERMINAL_FAILURE"),
        #"$template":             lambda StateIdx:   "TEMPLATE_%s"       % __nice(StateIdx),
        #"$pathwalker":           lambda StateIdx:   "PATH_WALKER_%s"    % __nice(StateIdx),
        #"$pathwalker-router":    lambda StateIdx:   "PATH_WALKER_%s_STATE_ROUTER" % __nice(StateIdx),
        #"$entry":                lambda StateIdx:   "_%s"               % __nice(StateIdx),
        #"$entry-stub":           lambda StateIdx:   "STATE_%s_STUB"     % __nice(StateIdx),
        "$reload":                lambda StateIdx:    map_label_to_state_index("STATE_%s_RELOAD"          % __nice(StateIdx)),
        "$drop-out-direct":       lambda StateIdx:    map_label_to_state_index("STATE_%s_DROP_OUT_DIRECT" % __nice(StateIdx)),
        #"$re-start":             lambda NoThing:    "__REENTRY_PREPARATION",
        #"$start":                lambda NoThing:    "__REENTRY",
        #"$init_state_fw_transition_block": lambda NoThing: "INIT_STATE_TRANSITION_BLOCK",
    }[Type](Index)

def _pure_position(LabelID):
    return "_%s" % __nice(LabelID)

def _position(NameOrTerminalID):
    return _pure_position(map_label_to_state_index(NameOrTerminalID))

__label_db = \
{
    "$terminal":              lambda TerminalIdx: _position("TERMINAL_%s"        % __nice(TerminalIdx)),
    "$terminal-direct":       lambda TerminalIdx: _position("TERMINAL_%s_DIRECT" % __nice(TerminalIdx)),
    "$terminal-general-bw":   lambda NoThing:     _position("TERMINAL_GENERAL_BACKWARD"),
    "$terminal-EOF":          lambda NoThing:     _position("TERMINAL_END_OF_STREAM"),
    "$terminal-FAILURE":      lambda NoThing:     _position("TERMINAL_FAILURE"),
    "$template":              lambda StateIdx:    "TEMPLATE_%s"       % __nice(StateIdx),
    "$pathwalker":            lambda StateIdx:    "PATH_WALKER_%s"    % __nice(StateIdx),
    "$pathwalker-router":     lambda StateIdx:    "PATH_WALKER_%s_STATE_ROUTER" % __nice(StateIdx),
    "$entry":                 lambda StateIdx:    "_%s"               % __nice(StateIdx),
    "$entry-stub":            lambda StateIdx:    "STATE_%s_STUB"     % __nice(StateIdx),
    "$reload":                lambda StateIdx:    _position("STATE_%s_RELOAD"          % __nice(StateIdx)),
    "$drop-out-direct":       lambda StateIdx:    _position("STATE_%s_DROP_OUT_DIRECT" % __nice(StateIdx)),
    "$re-start":              lambda NoThing:     "__REENTRY_PREPARATION",
    "$start":                 lambda NoThing:     "__REENTRY",
    "$init_state_fw_transition_block": lambda NoThing: "INIT_STATE_TRANSITION_BLOCK",
}

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
        self.code  = [ _pure_position(self.label), ":\n" ]
        if type(Code) == list: self.code.extend(Code)
        else:                  self.code.append(Code)

class Reference:
    def __init__(self, Type, Arg):
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

        self.reference_type = Type

    def __repr__(self):
        return self.code
