from   quex.engine.analyzer.state.drop_out        import DropOutGotoDoorId
from   quex.engine.analyzer.door_id_address_label import DoorID, \
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
        txt.append("%s\n" % Lng.GOTO(DoorID.global_end_of_pre_context_check()))
        return

    elif EngineType.is_BACKWARD_INPUT_POSITION():
        if DropOut.reachable_f:
            incidence_id = EngineType.incidence_id_of_bipd()
            txt.extend([ 
                1, '__quex_debug("pattern %i: backward input position detected\\n");\n' % incidence_id,
                1, "%s\n\n" % Lng.INPUT_P_INCREMENT(),
                1, "%s\n" % Lng.GOTO(DoorID.incidence(incidence_id)) \
            ])
        return

    elif isinstance(DropOut, DropOutGotoDoorId):
        txt.append("%s\n" % Lng.GOTO(DropOut.door_id))
        return

    txt.extend(
        Lng.COMMAND(x) for x in DropOut.get_command_list()
    )
    return 


