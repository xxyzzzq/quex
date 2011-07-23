from   quex.engine.analyzer.core import Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection

def do(txt, TheState, PositionRegisterMap):
    LanguageDB = Setup.language_db

    if isinstance(TheState.entry, Entry):
        __doors(txt, TheState.entry.get_positioner_db(), PositionRegisterMap)
        __accepter(txt, TheState.entry.get_accepter())
        return

    txt.append(LanguageDB.STATE_ENTRY(TheState))
    if isinstance(TheState.entry, EntryBackward):
        for pre_context_id in TheState.entry.pre_context_fulfilled_set:
            txt.append("    %s\n" % LanguageDB.ASSIGN("pre_context_%i_fulfilled_f" % pre_context_id, "true"))

    elif isinstance(TheState.entry, EntryBackwardInputPositionDetection):
        if TheState.entry.terminated_f: 
            txt.append("    %s\n" % LanguageDB.RETURN)

def __doors(txt, TheEntry, PositionRegisterMap):

    if len(PositionerDB) == 0:
        txt.append(LanguageDB.STATE_ENTRY(TheState))
        return

    def __do(Positioner):
        first_f = True
        for post_context_id, pre_context_id_list in Positioner:
            register     = PositionRegisterMap[post_context_id]
            register_str = "position[%i]" % register
            txt.append(
                LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                          LanguageDB.ASSIGN(register_str, "input_p")), 
            )
            first_f = False
        LanguageDB.END_IF(first_f)

    if TheEntry.is_uniform():
        # (*) Uniform state entries from all entering states.
        #     Assume that 'GOTO' can identify its uniform target states. Thus, no separate
        #     entries are required.
        for from_state_index, positioner in PositionerDB.iteritems():
            txt.append(LanguageDB.STATE_ENTRY(TheState, from_state_index))
        txt.append(LanguageDB.STATE_ENTRY(TheState))
        txt.append(__do(TheEntry.uniform_positioner()))
        return
    else:
        # (*) Non-uniform state entries
        for from_state_index, positioner in PositionerDB.iteritems():
            txt.append(LanguageDB.STATE_ENTRY(TheState, from_state_index))
            txt.append(__do(positioner))
            txt.append(LanguageDB.GOTO(TheState.index))
        txt.append(LanguageDB.STATE_ENTRY(TheState))

def __accepter(txt, Accepter):
    if len(Accepter) == 0: return

    first_f = True
    for pre_context_id_list, acceptance_id in TheState.entry.get_accepter():
        assert isinstance(acceptance_id, (int, long))
        txt.append(
            LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                      LanguageDB.ASSIGN("last_acceptance", "%i" % acceptance_id))
        )
        first_f = False
    LanguageDB.END_IF(first_f)
            
