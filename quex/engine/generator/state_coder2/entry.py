from   quex.engine.analyzer.core import Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection
from   quex.engine.state_machine.state_core_info import EngineTypes
from   quex.blackboard import setup as Setup

from   itertools import imap

def do(txt, TheState, TheAnalyzer):
    """Writes code for the state entry into 'txt'.

       RETURNS: True -- if further code for the transition block and the 
                        drop out is required.
                False -- if no further code is required.
    """
    LanguageDB          = Setup.language_db
    PositionRegisterMap = TheAnalyzer.position_register_map

    if  (not TheState.init_state_f) or \
        (TheState.engine_type == EngineTypes.BACKWARD_INPUT_POSITION): 
        txt.append("\n\n    %s\n" % LanguageDB.UNREACHABLE)
    else:
        txt.append("\n\n")

    if isinstance(TheState.entry, Entry):
        __doors(txt, TheState, PositionRegisterMap)
        __accepter(txt, TheState.entry.get_accepter())
        return True

    entry = TheState.entry
    if isinstance(entry, EntryBackward):
        LanguageDB.STATE_ENTRY(txt, TheState)
        for pre_context_id in entry.pre_context_fulfilled_set:
            txt.append("    %s\n" % LanguageDB.ASSIGN("pre_context_%i_fulfilled_f" % pre_context_id, "true"))

    elif isinstance(entry, EntryBackwardInputPositionDetection):
        LanguageDB.STATE_ENTRY(txt, TheState, BIPD_ID=entry.backward_input_positon_detector_sm_id)
        if entry.terminated_f: 
            txt.append('    __quex_debug("backward input position %i detected");\n' % \
                       entry.backward_input_positon_detector_sm_id)
            txt.append("    goto %s;\n" \
                       % LanguageDB.LABEL_NAME_BACKWARD_INPUT_POSITION_RETURN(entry.backward_input_positon_detector_sm_id))
            # No drop-out, no transition map required
            return False
    return True


def __doors(txt, TheState, PositionRegisterMap):
    LanguageDB = Setup.language_db
    TheEntry   = TheState.entry

    if len(TheEntry.positioner_db) == 0:
        LanguageDB.STATE_ENTRY(txt, TheState)
        return

    def __do(txt, Positioner):
        # The check 'if pre-context' + the jump take most likely more time
        # then simply assigning the position to the position register. So
        # simply omit the check. Collect all registers that store.
        register_set = set(imap(lambda post_context_id: PositionRegisterMap[post_context_id], 
                           Positioner.iterkeys()))
        for register in register_set:
            txt.append(
                " %s" % LanguageDB.ASSIGN(LanguageDB.POSITION_REGISTER(register), LanguageDB.INPUT_P), 
            )

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
        for from_state_index, positioner in TheEntry.get_positioner_db().iteritems():
            LanguageDB.STATE_ENTRY(txt, TheState, from_state_index, NewlineF=False)
            __do(txt, positioner)
            txt.append(" %s\n" % LanguageDB.GOTO(TheState.index))
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
            
