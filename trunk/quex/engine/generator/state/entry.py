from   quex.engine.analyzer.state.core                   import AnalyzerState
from   quex.engine.analyzer.door_id_address_label        import dial_db, \
                                                                IfDoorIdReferencedLabel, \
                                                                DoorID, \
                                                                Label
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
import quex.engine.generator.state.entry_door_tree       as     entry_door_tree

from quex.blackboard import setup as Setup, \
                            E_StateIndices, \
                            E_Commands

from operator import attrgetter

def do(TheState, TheAnalyzer, UnreachablePrefixF=True, LabelF=True):
    LanguageDB = Setup.language_db

    door_tree_root = entry_door_tree.do(TheState.index, TheState.entry.action_db)
    if not TheAnalyzer.is_init_state_forward(TheState.index):
        pre_txt = []
        if TheState.index != TheAnalyzer.init_state_index:
            pre_txt.append("\n\n    %s\n" % LanguageDB.UNREACHABLE)
        do_node(pre_txt, TheState.entry.action_db, door_tree_root)
        post_txt = []
    else:
        pre_txt, done_set = do_state_machine_entry(door_tree_root, TheState, TheAnalyzer)
        post_txt = [ "\n\n    %s\n" % LanguageDB.UNREACHABLE ]
        post_txt.extend(do_post(door_tree_root, TheState, done_set))
            
    pre_txt.append("    ")
    LanguageDB.STATE_DEBUG_INFO(pre_txt, TheState, TheAnalyzer)
    return pre_txt, post_txt

def do_core(txt, TheState):
    door_tree_root = entry_door_tree.do(TheState.index, TheState.entry.action_db)
    do_node(txt, TheState.entry.action_db, door_tree_root, LastChildF=False)

def do_state_machine_entry(door_tree_root, TheState, TheAnalyzer):
    action  = TheAnalyzer.get_action_at_state_machine_entry()
    assert action is not None
    door_id = action.door_id
    node    = entry_door_tree.find(door_tree_root, door_id)
    assert node is not None

    done_door_id_set = set()
    txt              = []
    while node is not None:
        code_action(txt, node, TheState.entry.action_db, GotoParentF=False)
        done_door_id_set.add(node.door_id)
        node = node.parent
    txt.append(IfDoorIdReferencedLabel(DoorID.transition_block(TheState.index)))
    return txt, done_door_id_set

def do_post(door_tree_root, TheState, DoneDoorIdSet):
    txt = []
    do_node(txt, TheState.entry.action_db, door_tree_root, LastChildF=False, DoneDoorIdSet=DoneDoorIdSet)
    # txt.append("    goto %s;\n" % Label.transition_block(TheState.index, GotoedF=True))
    return txt

def do_node(txt, ActionDb, Node, LastChildF=False, DoneDoorIdSet=None):
    """Recursive function: '__dive' -- Marked, TODO: implement by TreeWalker.
    """
    LanguageDB = Setup.language_db
    if Node.child_set is not None:
        LastI = len(Node.child_set) - 1
        for i, child in enumerate(sorted(Node.child_set, key=attrgetter("door_id"))):
            do_node(txt, ActionDb, child, LastChildF=(i==LastI), DoneDoorIdSet=DoneDoorIdSet)
    
    if DoneDoorIdSet is None or Node.door_id not in DoneDoorIdSet:
        # Careful: "GotoParentF = not LastChildF" because of 'DoneDoorIdSet'
        code_action(txt, Node, ActionDb, GotoParentF=True) 

def code_action(txt, Node, ActionDb, GotoParentF):
    LanguageDB = Setup.language_db
    txt.append(IfDoorIdReferencedLabel(Node.door_id))

    comment_door(txt, Node, ActionDb)

    action_txt = [ LanguageDB.COMMAND(command) for command in Node.command_list ]
    if Node.parent is not None and GotoParentF: 
        action_txt.append(1)
        action_txt.append(LanguageDB.GOTO_BY_DOOR_ID(Node.parent.door_id))
    txt.extend(action_txt)
    txt.extend("\n")

def comment_door(txt, Node, ActionDb):
    LanguageDB = Setup.language_db

    # If the door is entered by another state, write a comment from where it is entered.
    transition_id_list = ActionDb.get_transition_id_list(Node.door_id)
    if len(transition_id_list) != 0:
        txt.append(" ")
        LanguageDB.COMMENT(txt, "".join([ "(%s from %s) " % (x.target_state_index, x.source_state_index) for x in transition_id_list])[:-1])
    else:
        txt.append("\n") 

