from   quex.engine.analyzer.core import Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection
from   quex.blackboard import setup as Setup

def do(txt, TheState, PositionRegisterMap):
    LanguageDB = Setup.language_db

    if not TheState.init_state_f: txt.append("\n\n    %s\n" % LanguageDB.UNREACHABLE)
    else:                         txt.append("\n\n")

    if isinstance(TheState.entry, Entry):
        __doors(txt, TheState, PositionRegisterMap)
        __accepter(txt, TheState.entry.get_accepter())
        return

    LanguageDB.STATE_ENTRY(txt, TheState)
    if isinstance(TheState.entry, EntryBackward):
        for pre_context_id in TheState.entry.pre_context_fulfilled_set:
            txt.append("    %s\n" % LanguageDB.ASSIGN("pre_context_%i_fulfilled_f" % pre_context_id, "true"))

    elif isinstance(TheState.entry, EntryBackwardInputPositionDetection):
        if TheState.entry.terminated_f: 
            txt.append("    %s\n" % LanguageDB.RETURN)

def __doors(txt, TheState, PositionRegisterMap):
    LanguageDB = Setup.language_db
    TheEntry   = TheState.entry

    if len(TheEntry.positioner_db) == 0:
        LanguageDB.STATE_ENTRY(txt, TheState)
        return

    def __do(txt, Positioner):
        first_f = True
        for post_context_id, pre_context_id_list in Positioner:
            register     = PositionRegisterMap[post_context_id]
            register_str = "position[%i]" % register
            txt.append(
                LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                          LanguageDB.ASSIGN(register_str, "input_p")), 
            )
            first_f = False
        if len(Positioner) != 0:
            txt.append(LanguageDB.END_IF())

    if TheEntry.is_uniform():
        # (*) Uniform state entries from all entering states.
        #     Assume that 'GOTO' can identify its uniform target states. Thus, no separate
        #     entries are required.
        for from_state_index, positioner in TheEntry.positioner_db.iteritems():
            LanguageDB.STATE_ENTRY(txt, TheState, from_state_index, NewlineF=False)
            txt.append("%s\n" % LanguageDB.GOTO(TheState.index))
        LanguageDB.STATE_ENTRY(txt, TheState)
        __do(txt, TheEntry.uniform_positioner())
        return
    else:
        # (*) Non-uniform state entries
        for from_state_index, positioner in TheEntry.positioner_db.iteritems():
            LanguageDB.STATE_ENTRY(txt, TheState, from_state_index)
            __do(txt, positioner)
            txt.append(LanguageDB.GOTO(TheState.index))
        LanguageDB.STATE_ENTRY(txt, TheState)

def __accepter(txt, Accepter):
    LanguageDB = Setup.language_db
    if len(Accepter) == 0: return

    first_f = True
    for pre_context_id_list, acceptance_id in Accepter:
        assert isinstance(acceptance_id, (int, long))
        txt.append(
            LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                      LanguageDB.ASSIGN("last_acceptance", "%i" % acceptance_id))
        )
        first_f = False
    txt.append(LanguageDB.END_IF())
            
