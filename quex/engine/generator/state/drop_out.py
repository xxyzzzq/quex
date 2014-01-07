from   quex.engine.analyzer.state.drop_out        import DropOutGotoDoorId
from   quex.engine.analyzer.door_id_address_label import Label, \
                                                         DoorID, \
                                                         IfDoorIdReferencedLabel
from   quex.blackboard                            import E_IncidenceIDs, E_StateIndices, \
                                                         E_TransitionN, E_PostContextIDs, E_PreContextIDs, \
                                                         Lng

#drop_out.do(txt, TheState.index, TheState.drop_out, TheAnalyzer)
#drop_out.do(txt, TheState.index, uniform_drop_out, TheAnalyzer, \
#            DefineLabelF=False, MentionStateIndexF=False)
#drop_out.do(case_txt, TheState.index, drop_out_object, TheAnalyzer, 
#            DefineLabelF=False, MentionStateIndexF=False)

def do(txt, StateIndex, DropOut, TheAnalyzer, DefineLabelF=True, MentionStateIndexF=True):
    
    EngineType = TheAnalyzer.engine_type
    if DefineLabelF:
        txt.append(IfDoorIdReferencedLabel(DoorID.drop_out(StateIndex)))

    if MentionStateIndexF:
        txt.append(1)
        txt.append("__quex_debug_drop_out(%i);\n" % StateIndex)

    if EngineType.is_BACKWARD_PRE_CONTEXT():
        txt.append(1)
        txt.append("%s\n" % Lng.GOTO_BY_DOOR_ID(DoorID.global_end_of_pre_context_check()))
        return

    elif EngineType.is_BACKWARD_INPUT_POSITION():
        if DropOut.reachable_f:
            incidence_id = EngineType.incidence_id_of_bipd()
            txt.extend([ 
                1, '__quex_debug("pattern %i: backward input position detected\\n");\n' % incidence_id,
                1, "%s\n\n" % Lng.INPUT_P_INCREMENT(),
                1, "%s\n" % Lng.GOTO_BY_DOOR_ID(DoorID.incidence(incidence_id)) \
            ])
        return

    elif isinstance(DropOut, DropOutGotoDoorId):
        txt.extend([
            1, '__quex_debug("Character counting terminated.\\n");\n',
            1, "%s\n" % Lng.GOTO_BY_DOOR_ID(DropOut.door_id) \
        ])
        return

    info = DropOut.trivialize()
    # (1) Trivial Solution
    if info is not None:
        for i, easy in enumerate(info):
            Lng.IF_PRE_CONTEXT(txt, i == 0, easy[0].pre_context_id, position_and_goto(EngineType, easy[1]))
        return

    # (2) Separate: Pre-Context Check and Routing to Terminal
    # (2.1) Pre-Context Check
    for i, element in enumerate(DropOut.get_acceptance_checker()):
        if     element.pre_context_id == E_PreContextIDs.NONE \
           and element.acceptance_id  == E_IncidenceIDs.VOID: 
               break
        txt.append(1)
        Lng.IF_PRE_CONTEXT(txt, i == 0, element.pre_context_id, 
                                  Lng.ASSIGN("last_acceptance", 
                                                    Lng.ACCEPTANCE(element.acceptance_id)))
        if element.pre_context_id == E_PreContextIDs.NONE: 
            break # No check after the unconditional acceptance

    # (2.2) Routing to Terminal
    case_list = [
        (Lng.ACCEPTANCE(element.acceptance_id), position_and_goto(EngineType, element))
        for element in DropOut.get_terminal_router()
    ]

    txt.extend(Lng.SELECTION("last_acceptance", case_list))

def position_and_goto(EngineType, X):
    
    # If the pattern requires backward input position detection, then
    # jump to the entry of the detector. (This is a very seldom case)
    if EngineType.is_FORWARD():
        bipd_entry_door_id = EngineType.bipd_entry_door_id_db.get(X.acceptance_id)
        if bipd_entry_door_id is not None:                        
            return Lng.GOTO_BY_DOOR_ID(bipd_entry_door_id) 

    # Position the input pointer and jump to terminal.
    positioning_str   = Lng.POSITIONING(X)
    if len(positioning_str) != 0: positioning_str += "\n"
    goto_terminal_str = Lng.GOTO_BY_DOOR_ID(DoorID.incidence(X.acceptance_id))
    return [
        0, positioning_str, "\n" if len(positioning_str) != 0 else "",
        0, goto_terminal_str
    ]

