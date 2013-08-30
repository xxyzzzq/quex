from   quex.engine.analyzer.state.core                   import AnalyzerState
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
import quex.engine.generator.state.entry_door_tree       as     entry_door_tree

from quex.blackboard import setup as Setup, \
                            E_StateIndices

from operator import attrgetter

def do(txt, TheState, TheAnalyzer, UnreachablePrefixF=True, LabelF=True):
    """Writes code for the state entry into 'txt'.

       RETURNS: True -- if further code for the transition block and the 
                        drop out is required.
                False -- if no further code is required.
    """
    assert isinstance(TheState, AnalyzerState)
    assert type(UnreachablePrefixF) == bool
    assert type(LabelF) == bool
    LanguageDB = Setup.language_db

    txt.append("\n\n")
    if      UnreachablePrefixF \
        and (    (not TheState.init_state_f) \
              or (TheState.engine_type.is_BACKWARD_INPUT_POSITION())): 
        txt.append(1)
        txt.append("%s\n" % LanguageDB.UNREACHABLE)

    if TheAnalyzer.engine_type.is_BACKWARD_INPUT_POSITION():
        BIPD_ID = TheAnalyzer.state_machine_id
    else:
        BIPD_ID = None

    return do_core(txt, TheState.index, TheState.entry.action_db)

def do_core(txt, StateIndex, ActionDb):
    door_tree_root = entry_door_tree.do(StateIndex, ActionDb)

    do_node(txt, ActionDb, door_tree_root, LastChildF=False, BIPD_ID=BIPD_ID)

    return True

def do_node(txt, ActionDb, Node, LastChildF=False, BIPD_ID=None):
    """Recursive function: '__dive' -- Marked, TODO: implement by TreeWalker.
    """
    LanguageDB = Setup.language_db
    if Node.child_set is not None:
        LastI = len(Node.child_set) - 1
        for i, child in enumerate(sorted(Node.child_set, key=attrgetter("door_id"))):
            do_node(txt, ActionDb, child, LastChildF=(i==LastI), BIPD_ID=BIPD_ID)
    
    # If the door can be a 'goto' target, the label needs to be defined.
    door_label = map_door_id_to_label(Node.door_id)

    if door_label is not None:
        txt.append(door_label)

    comment_door(txt, Node, ActionDb)

    action_txt = [ LanguageDB.COMMAND(command) for command in Node.command_list ]
    if Node.parent is not None and not LastChildF: 
        action_txt.append(1)
        action_txt.append(LanguageDB.GOTO_BY_DOOR_ID(Node.parent.door_id))
    txt.extend(action_txt)
    txt.extend("\n")

def do_entry_from_NONE(txt, TheState):
    LanguageDB = Setup.language_db
    action = TheState.entry.action_db.get_action(TheState.index, E_StateIndices.NONE)
    if action is None: 
        return
    txt.extend(LanguageDB.COMMAND(command) for command in action.command_list) 
    
def comment_door(txt, Node, ActionDb):
    LanguageDB = Setup.language_db

    # If the door is entered by another state, write a comment from where it is entered.
    transition_id_list = ActionDb.get_transition_id_list(Node.door_id)
    if len(transition_id_list) != 0:
        txt.append(" ")
        LanguageDB.COMMENT(txt, "".join([ "(%s from %s) " % (x.target_state_index, x.source_state_index) for x in transition_id_list])[:-1])
    else:
        txt.append("\n") 

