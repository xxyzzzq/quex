from   quex.engine.analyzer.core import Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection

def do(txt, TheState, TheAnalyzer)):
    LanguageDB = Setup.language_db

    if isinstance(TheState.entry, Entry):
        __doors(txt, TheState.entry, TheAnalyzer)
        __accepter(txt, TheAnalyzer.entry.get_accepter())

    elif isinstance(TheState.entry, EntryBackward):
        for pre_context_id in TheState.entry.pre_context_fulfilled_set:
            txt.append("    %s\n" % LanguageDB.ASSIGN("pre_context_%i_fulfilled_f" % pre_context_id, "true"))

    elif isinstance(TheState.entry, EntryBackwardInputPositionDetection):
        if TheState.entry.terminated_f: 
            txt.append("    %s\n" % LanguageDB.RETURN)

def __doors(TheEntry, TheAnalyzer):
    if len(TheState.entry.positioner) != 0:
        first_f = True
        for register, pre_context_id_list in TheState.entry.get_positioner():
            if register == PostContextIDs.NONE: register_str = "last_acceptance"
            else:                               register_str = "position[%i]" % register
            txt.append(
                LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                          LanguageDB.ASSIGN(register_str, "input_p")), 
            )
            first_f = False
        LanguageDB.END_IF(first_f)

def __accepter(txt, Accepter, TheAnalyzer):
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
            
