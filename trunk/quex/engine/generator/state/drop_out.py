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

    if MentionStateIndexF:
        txt.append(1)
        txt.append("__quex_debug_drop_out(%i);\n" % StateIndex)

    txt.extend(
        Lng.GOTO(TheAnalyzer.drop_out_DoorID(StateIndex))
    )
    return 


