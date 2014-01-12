from   quex.engine.analyzer.state.core                   import AnalyzerState
from   quex.engine.analyzer.door_id_address_label        import dial_db, \
                                                                IfDoorIdReferencedLabel, \
                                                                DoorID
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
import quex.engine.generator.state.entry_door_tree       as     entry_door_tree
from   quex.engine.tools                                 import none_is_None

from quex.blackboard import Lng, \
                            E_StateIndices, \
                            E_Commands

from operator import attrgetter

def do(TheState, TheAnalyzer, UnreachablePrefixF=True, LabelF=True):
    door_tree_root = entry_door_tree.do(TheState.index, TheState.entry)
    if not TheAnalyzer.is_init_state_forward(TheState.index):
        pre_txt = []
        if TheState.index != TheAnalyzer.init_state_index:
            pre_txt.append("\n\n    %s\n" % Lng.UNREACHABLE)
        do_node(pre_txt, TheState.entry, door_tree_root)
        post_txt = []
    else:
        pre_txt, done_set = do_state_machine_entry(door_tree_root, TheState, TheAnalyzer)
        post_txt = [ "\n\n    %s\n" % Lng.UNREACHABLE ]
        post_txt.extend(do_post(door_tree_root, TheState, done_set))
            
    pre_txt.append("    ")
    Lng.STATE_DEBUG_INFO(pre_txt, TheState, TheAnalyzer)
    return pre_txt, post_txt

def do_core(txt, TheState):
    door_tree_root = entry_door_tree.do(TheState.index, TheState.entry)
    do_node(txt, TheState.entry, door_tree_root, LastChildF=False)

def do_state_machine_entry(door_tree_root, TheState, TheAnalyzer):
    action  = TheAnalyzer.get_action_at_state_machine_entry()
    assert action is not None
    door_id = action.door_id
    node    = entry_door_tree.find(door_tree_root, door_id)
    assert node is not None

    done_door_id_set = set()
    txt              = []
    while node is not None:
        code_action(txt, node, TheState.entry, GotoParentF=False)
        done_door_id_set.add(node.door_id)
        node = node.parent
    txt.append(IfDoorIdReferencedLabel(DoorID.transition_block(TheState.index)))
    return txt, done_door_id_set

def do_post(door_tree_root, TheState, DoneDoorIdSet):
    txt = []
    do_node(txt, TheState.entry, door_tree_root, LastChildF=False, DoneDoorIdSet=DoneDoorIdSet)
    return txt

def do_node(txt, ActionDb, Node, LastChildF=False, DoneDoorIdSet=None):
    """Recursive function: '__dive' -- Marked, TODO: implement by TreeWalker.
    """
    
    if Node.child_set is not None:
        LastI = len(Node.child_set) - 1
        for i, child in enumerate(sorted(Node.child_set, key=attrgetter("door_id"))):
            do_node(txt, ActionDb, child, LastChildF=(i==LastI), DoneDoorIdSet=DoneDoorIdSet)
    
    if DoneDoorIdSet is None or Node.door_id not in DoneDoorIdSet:
        # Careful: "GotoParentF = not LastChildF" because of 'DoneDoorIdSet'
        code_action(txt, Node, ActionDb, GotoParentF=True) 
        # assert none_is_None(txt)

def code_action(txt, Node, ActionDb, GotoParentF):
    
    txt.append(IfDoorIdReferencedLabel(Node.door_id))
    comment_door(txt, Node, ActionDb)
    txt.extend([ 
        Lng.COMMAND(command) 
        for command in Node.command_list 
    ])
    if Node.parent is not None and GotoParentF: 
        txt.append("    %s\n" % Lng.GOTO(Node.parent.door_id))
    txt.append("\n")

def comment_door(txt, Node, ActionDb):
    
    # If the door is entered by another state, write a comment from where it is entered.
    transition_id_list = ActionDb.get_transition_id_list(Node.door_id)
    if len(transition_id_list) != 0:
        txt.append(" ")
        txt.append(
            Lng.COMMENT("".join([ 
                "(%s from %s) " % (x.target_state_index, x.source_state_index) for x in transition_id_list])[:-1]
            )
        )
    else:
        txt.append("\n") 

