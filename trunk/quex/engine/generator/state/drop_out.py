from   quex.engine.generator.languages.address    import Label, \
                                                         LabelIfDoorIdReferenced, \
                                                         map_door_id_to_address
from   quex.engine.analyzer.state.entry_action    import DoorID
from   quex.blackboard                            import E_AcceptanceIDs, E_StateIndices, \
                                                         E_TransitionN, E_PostContextIDs, E_PreContextIDs, \
                                                         setup as Setup

#drop_out.do(txt, TheState.index, TheState.drop_out, TheAnalyzer)
#drop_out.do(txt, TheState.index, uniform_drop_out, TheAnalyzer, \
#            DefineLabelF=False, MentionStateIndexF=False)
#drop_out.do(case_txt, TheState.index, drop_out_object, TheAnalyzer, 
#            DefineLabelF=False, MentionStateIndexF=False)

def do(txt, StateIndex, DropOut, TheAnalyzer, DefineLabelF=True, MentionStateIndexF=True):
    LanguageDB = Setup.language_db

    if DefineLabelF:
        txt.append(LabelIfDoorIdReferenced(DoorID.drop_out(StateIndex)))

    if MentionStateIndexF:
        txt.append(1)
        txt.append("__quex_debug_drop_out(%i);\n" % StateIndex)

    if TheAnalyzer.engine_type.is_BACKWARD_PRE_CONTEXT():
        txt.append(1)
        txt.append("%s\n" % LanguageDB.GOTO_BY_DOOR_ID(DoorID.global_end_of_pre_context_check()))
        return

    elif TheAnalyzer.engine_type.is_BACKWARD_INPUT_POSITION():
        if DropOut.reachable_f:
            # 'TheAnalyzer' is the state machine which does the backward input position
            # detection. => TheAnalyzer.state_machine_id = id of the backward input 
            # position detector.
            txt.extend([ 
                1, '__quex_debug("backward input position %i detected\\n");\n' \
                   % TheAnalyzer.state_machine_id,
                1, "%s\n\n" % LanguageDB.INPUT_P_INCREMENT(),
                1, "goto %s;\n" \
                   % Label.backward_input_position_detector_return(TheAnalyzer.state_machine_id, GotoedF=True)
            ])
        return

    def position_and_goto(X):
        positioning_str   = LanguageDB.POSITIONING(easy[1])
        if len(positioning_str) != 0: positioning_str += "\n"
        goto_terminal_str = LanguageDB.GOTO_BY_DOOR_ID(DoorID.acceptance(easy[1].acceptance_id))
        return [
            0, positioning_str, "\n" if len(positioning_str) != 0 else "",
            0, goto_terminal_str
        ]

    info = DropOut.trivialize()
    # (1) Trivial Solution
    if info is not None:
        for i, easy in enumerate(info):
            LanguageDB.IF_PRE_CONTEXT(txt, i == 0, easy[0].pre_context_id, position_and_goto(easy[1]))
        return

    # (2) Separate: Pre-Context Check and Routing to Terminal
    # (2.1) Pre-Context Check
    for i, element in enumerate(DropOut.get_acceptance_checker()):
        if     element.pre_context_id == E_PreContextIDs.NONE \
           and element.acceptance_id  == E_AcceptanceIDs.VOID: 
               break
        txt.append(1)
        LanguageDB.IF_PRE_CONTEXT(txt, i == 0, element.pre_context_id, 
                                  LanguageDB.ASSIGN("last_acceptance", 
                                                    LanguageDB.ACCEPTANCE(element.acceptance_id)))
        if element.pre_context_id == E_PreContextIDs.NONE: 
            break # No check after the unconditional acceptance

    # (2.2) Routing to Terminal
    case_list = [
        (LanguageDB.ACCEPTANCE(element.acceptance_id), position_and_goto(element))
        for element in DropOut.get_terminal_router()
    ]

    txt.extend(LanguageDB.SELECTION("last_acceptance", case_list))

