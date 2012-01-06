from   quex.engine.analyzer.state_entry import Entry, \
                                               Action_StoreInputPosition
from   quex.blackboard import setup as Setup, \
                              E_EngineTypes, \
                              E_PreContextIDs, \
                              E_StateIndices

from operator import attrgetter

def do(txt, TheState, TheAnalyzer, UnreachablePrefixF=True, LabelF=True):
    """Writes code for the state entry into 'txt'.

       RETURNS: True -- if further code for the transition block and the 
                        drop out is required.
                False -- if no further code is required.
    """
    LanguageDB = Setup.language_db

    if      UnreachablePrefixF \
        and (    (not TheState.init_state_f) \
              or (TheState.engine_type == E_EngineTypes.BACKWARD_INPUT_POSITION)): 
        txt.append("\n\n    %s\n" % LanguageDB.UNREACHABLE)
    else:
        txt.append("\n\n")

    if TheState.engine_type == E_EngineTypes.BACKWARD_INPUT_POSITION:
        BIPD_ID = TheAnalyzer.state_machine_id
    else:
        BIPD_ID = None

    doit(txt, TheState, TheState.entry.door_tree_root, LastChildF=False, BIPD_ID=BIPD_ID)

    return True

def doit(txt, TheState, Node, LastChildF=False, BIPD_ID=None):
    LanguageDB = Setup.language_db
    LastI      = len(Node.child_list) - 1
    for i, child in enumerate(sorted(Node.child_list, key=attrgetter("identifier"))):
        doit(txt, TheState, child, LastChildF=(i==LastI), BIPD_ID=BIPD_ID)
    
    if     len(Node.child_list) == 0 \
       and (    len(Node.door_list) == 0 \
            or (len(Node.door_list) == 1 and Node.door_list[0] == E_StateIndices.NONE)):
        pass
    else:
        # If the door can be a 'goto' target, the label needs to be defined.
        LanguageDB.COMMENT(txt, "State: %s; DoorIndex=%s; %s\n" % (TheState.index, Node.identifier, BIPD_ID))
        if TheState.init_state_f and BIPD_ID is not None:
            txt.append(LanguageDB.LABEL_BACKWARD_INPUT_POSITION_DETECTOR(BIPD_ID))
        else:
            txt.append(LanguageDB.LABEL(TheState.index, DoorIndex=Node.identifier, NewlineF=False))

        if len(Node.door_list) != 0:
            # If the door is entered by another state, write a comment from where it is entered.
            LanguageDB.COMMENT(txt, " from " + "".join([ "(%s) " % x for x in Node.door_list]))
        else:
            txt.append("\n") 

    action_txt = [ LanguageDB.ACTION(action) for action in Node.common_action_list ]
    if Node.parent is not None and not LastChildF: 
        action_txt.append(LanguageDB.GOTO(TheState.index, DoorIndex=Node.parent.identifier))
    txt.extend(action_txt)

def _doors(txt, TheState, LabelF):
    LanguageDB = Setup.language_db
    TheEntry   = TheState.entry

    if TheEntry.door_number() == 0:
        if LabelF: LanguageDB.STATE_ENTRY(txt, TheState)
        return

    def __do(txt, Door):
        # The check 'if pre-context' + the jump take most likely more time
        # then simply assigning the position to the position register. So
        # simply omit the check. Collect all registers that store.
        for action in (x for x in Door if isinstance(x, Action_StoreInputPosition)):
            register = LanguageDB.POSITION_REGISTER(action.position_register)
            value    = LanguageDB.INPUT_P()
            if action.offset != 0: value = "%s - %i" % (value, action.offset)
            txt.append(
                " %s" % LanguageDB.ASSIGN(register, value), 
            )

    prototype = TheEntry.get_uniform_door_prototype()
    if prototype is not None:
        # (*) Uniform state entries from all entering states.
        #     Assume that 'GOTO' can identify its independent_of_source_state target states. 
        #     Thus, no separate entries are required.
        if LabelF: LanguageDB.STATE_ENTRY(txt, TheState)
        __do(txt, prototype)
        return
    else:
        # (*) Non-independent_of_source_state state entries
        for from_state_index, door in TheEntry.get_positioner_db().iteritems():
            # if TheEntry.has_special_door_from_state(from_state_index):
            LanguageDB.STATE_ENTRY(txt, TheState, from_state_index, NewlineF=False)
            __do(txt, door)
            txt.append(" %s\n" % LanguageDB.GOTO(TheState.index))

        if LabelF: LanguageDB.STATE_ENTRY(txt, TheState)

def _accepter(txt, Accepter):
    LanguageDB = Setup.language_db
    if len(Accepter) == 0: return

    first_f = True
    for action in sorted(Accepter, key=attrgetter("acceptance_id")):
        txt.append(
            LanguageDB.IF_PRE_CONTEXT(first_f, action.pre_context_id, 
                                      LanguageDB.ASSIGN("last_acceptance", LanguageDB.ACCEPTANCE(action.acceptance_id)))
        )
        if action.pre_context_id == E_PreContextIDs.NONE: break
        first_f = False
            
