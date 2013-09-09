from   quex.engine.generator.languages.address    import Label, \
                                                         LabelIfDoorIdReferenced, \
                                                         map_door_id_to_address
from   quex.engine.analyzer.state.entry_action    import DoorID
from   quex.blackboard                            import E_AcceptanceIDs, E_StateIndices, \
                                                         E_TransitionN, E_PostContextIDs, E_PreContextIDs, \
                                                         setup as Setup

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

    info = DropOut.trivialize()
    # (1) Trivial Solution
    if info is not None:
        for i, easy in enumerate(info):
            consequence = []
            if easy[1].positioning != 0:
                if easy[1].positioning == E_TransitionN.VOID: register = easy[1].position_register
                else:                                         register = E_PostContextIDs.NONE
                positioning_str = "%s\n" % LanguageDB.POSITIONING(easy[1].positioning, register)
                consequence.append(0)
                consequence.append(positioning_str)
                consequence.append(0)

            goto_terminal_str = "%s" % LanguageDB.GOTO_BY_DOOR_ID(DoorID.acceptance(easy[1].acceptance_id))
            consequence.append(0)
            consequence.append(goto_terminal_str)
            LanguageDB.IF_PRE_CONTEXT(txt, i == 0, easy[0].pre_context_id, consequence)
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
    # (2.2.1) If the positioning is the same for all entries (except the FAILURE)
    #         then, again, the routing may be simplified:
    #router    = DropOut.router
    #prototype = (router[0].positioning, router[0].position_register)
    #simple_f  = True
    #for element in islice(router, 1, None):
    #    if element.acceptance_id == E_AcceptanceIDs.FAILURE: continue
    #    if prototype != (element.positioning, element.position_register): 
    #        simple_f = False
    #        break

    #if simple_f:
    #    txt.append("    %s\n    %s\n" % 
    #               (LanguageDB.POSITIONING(element.positioning, element.position_register), 
    #                LanguageDB.GOTO_BY_DOOR_ID(DoorID.acceptance(E_AcceptanceIDs.VOID))
    #else:
    case_list = []
    for element in DropOut.get_terminal_router():
        if element.positioning == E_TransitionN.VOID: register = element.position_register
        else:                                         register = None
        case_list.append((LanguageDB.ACCEPTANCE(element.acceptance_id), 
                          "%s %s" % \
                          (LanguageDB.POSITIONING(element.positioning, register),
                           LanguageDB.GOTO_BY_DOOR_ID(DoorID.acceptance(element.acceptance_id)))))

    txt.extend(LanguageDB.SELECTION("last_acceptance", case_list))

