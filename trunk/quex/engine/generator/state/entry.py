from   quex.engine.analyzer.core import Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection, \
                                        Action_StoreInputPosition
from   quex.blackboard import setup as Setup, \
                              E_EngineTypes, \
                              E_PreContextIDs

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

    entry = TheState.entry

    if isinstance(entry, Entry):
        _doors(txt, TheState, LabelF)
        _accepter(txt, TheState.entry.get_accepter())

    elif isinstance(entry, EntryBackward):
        LanguageDB.STATE_ENTRY(txt, TheState)
        for pre_context_id in entry.pre_context_fulfilled_set:
            txt.append("    %s\n" % LanguageDB.ASSIGN("pre_context_%i_fulfilled_f" % pre_context_id, "true"))

    elif isinstance(entry, EntryBackwardInputPositionDetection):
        # Backward input position detectors are always isolated state machines.
        # => TheAnalyzer.state_machine_id = id of the backward input position detector.
        LanguageDB.STATE_ENTRY(txt, TheState, BIPD_ID=TheAnalyzer.state_machine_id)
    return True

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
            
