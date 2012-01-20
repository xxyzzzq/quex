from   quex.blackboard import setup as Setup, \
                              E_EngineTypes, \
                              E_PreContextIDs, \
                              E_StateIndices

from operator import attrgetter

def do(txt, TheState, TheAnalyzer, UnreachablePrefixF=True, LabelF=True):
    """Writes code for the state entry into 'txt'.

       RETURNS: True -- if further code for the transition block and the 
                        drop out is required.
                False -- if no further code is required.
    """
    LanguageDB = Setup.language_db

    txt.append("\n\n")
    if      UnreachablePrefixF \
        and (    (not TheState.init_state_f) \
              or (TheState.engine_type == E_EngineTypes.BACKWARD_INPUT_POSITION)): 
        txt.append("    %s\n" % LanguageDB.UNREACHABLE)

    if TheState.engine_type == E_EngineTypes.BACKWARD_INPUT_POSITION:
        BIPD_ID = TheAnalyzer.state_machine_id
    else:
        BIPD_ID = None

    doit(txt, TheState, TheState.entry.door_tree_root, LastChildF=False, BIPD_ID=BIPD_ID)

    return True

def doit(txt, TheState, Node, LastChildF=False, BIPD_ID=None):
    LanguageDB = Setup.language_db
    LastI      = len(Node.child_list) - 1
    for i, child in enumerate(sorted(Node.child_list, key=attrgetter("identifier"))):
        doit(txt, TheState, child, LastChildF=(i==LastI), BIPD_ID=BIPD_ID)
    
    # If the door can be a 'goto' target, the label needs to be defined.
    if TheState.init_state_f and BIPD_ID is not None:
        txt.append(LanguageDB.LABEL_BACKWARD_INPUT_POSITION_DETECTOR(BIPD_ID))
    else:
        txt.append(LanguageDB.LABEL_BY_DOOR_ID(Node.door_id))

    comment_door(txt, TheState)

    action_txt = [ LanguageDB.COMMAND(command) for command in Node.common_command_list ]
    if Node.parent is not None and not LastChildF: 
        action_txt.append(LanguageDB.GOTO_BY_DOOR_ID(TheState.index, Node.parent.door_id))
    txt.extend(action_txt)

def comment_door(txt, TheState):
    # If the door is entered by another state, write a comment from where it is entered.
    return
    if len(Node.door_list) != 0:
        txt.append(" ")
        LanguageDB.COMMENT(txt, "from " + "".join([ "(%s) " % x for x in Node.door_list])[:-1])
    else:
        txt.append("\n") 

