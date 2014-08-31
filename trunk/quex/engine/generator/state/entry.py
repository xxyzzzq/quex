"""A state can be entered from multiple states and the actions performed upon
entry may differ, and partly be the same. A 'CommandTree' organizes command 
lists efficiently similarities. This module codes a command tree where its
leafs are the entries from other states.

                from X               from Y             from Z
                   |                    |                  |
                   |                    |                  |   
             .-------------.      .-------------.    .-------------.
             |DoorID:      |      |DoorID:      |    |DoorID:      |
             | CommandList |      | CommandList |    | CommandList |
             '-------------'      '-------------'    '-------------'
               parent \             / parent               / parent
                       \           /                      /
                      .-------------.                    /
                      |DoorID:      |                   /
                      | CommandList |                  /
                      '-------------'                 /
                                   \ parent          /
                                    \               /
                                  .-------------------.
                                  | Root-DoorID       |
                                  |   TransitionMap   |
                                     ...

NOTE: 
    
The code of an entry node is only implemented if the entry is actually 
goto-ed. Any command list may also contain goto-s. The goto-s in the command
lists influence the set of gotoed labels depending on their entry being
goto-ed. 

(C) Frank-Rene Schaefer
_______________________________________________________________________________
"""
from   quex.engine.analyzer.door_id_address_label import IfDoorIdReferencedLabel, \
                                                         DoorID
from   quex.engine.analyzer.commands.tree         import CommandTree
from   quex.engine.tools                          import flatten_list_of_lists
from   quex.blackboard                            import Lng, E_Cmd

@typed(FirstF=bool)
def do(TheState):
    """Generate code for the entry into a state from multiple different states.

    RETURNS: [0] Code to be 'pasted' in from of the transition map
             [1] Code to be pasted after the transition map. 
                 None -- if there is none.

    The case where [1] is not None, is actually a special case. It is the case
    of the global entry into the state machine / analyzer function. 

    The actions (CommandLists) to be executed may differ depending from where
    the state is entered. On the other hand, there may be shared commands in
    between the doors. To take profit from similarities, command lists are
    organized in a command tree as explained in the entry of the file.
    """
    cmd_tree = CommandTree.from_AnalyzerState(TheState)

    done_set = set()
    global_entry_door_id = TheState.get_global_entry_door_id()
    if global_entry_door_id is not None:
        pre_txt  = do_from_leaf_to_root(CmdTree, done_set, global_entry_door_id,
                                        GlobalEntryF=True)
        post_txt = []
        ref      = post_txt
    else:
        pre_txt  = ["\n\n    %s\n" % Lng.UNREACHABLE]
        post_txt = None
        ref      = pre_txt

    ref.extend(
        do_leafs(cmd_tree, TheState, done_set)
    )

    return pre_txt, post_txt

def do_leafs(CmdTree, OuterDoorIdSet, done_set):
    """Create code starting from the 'leafs' of the command tree. The leafs are 
    the entry points from other states, i.e. the 'doors'.

    RETURNS: List of strings.
    """
    txt_list = []
    for door_id in OuterDoorIdSet:
        if door_id in done_set: continue
        txt_list.append(
            do_from_leaf_to_root(CmdTree, done_set, DoorId)
        )

    # Flatten the list of lists, where the longest list has to come last.
    return flatten_it_list_of_lists(sorted(txt_list, sort_key=lambda x: len(x)))

def do_from_leaf_to_root(CmdTree, LeafDoorId, done_set, GlobalEntryF=False):
    """Code the sequence from a leaf of the command tree to its root. This
    avoids unnecessary gotos from outer nodes to their parents. It stops,
    whenever a parent is already implemented.  Then, the function 'code()'
    automatically inserts a 'goto parent' at the end of the node.

    RETURNS: list of strings 
    
    The list of string implements nodes from a command tree leaf over all of
    its parents to the root, or the first already implemented parent.
    """
    def from_leaf_to_root():
        """Starts from a given leaf node (given by LeafDoorId) and iterates
        through all of its parents until it reaches the root of the command
        tree.
        
        YIELDS: Command tree node
        """
        node = CmdTree.door_db[LeafDoorId]
        while node is not None:
            done_set.add(node.door_id)
            yield node
            node = node.parent

    txt = [
        Lng.STATE_DEBUG_INFO(TheState, GlobalEntryF)
    ]

    txt.extend(
        __code(node, TheState.entry, done_set)
        for node, leaf_f in from_leaf_to_root(CmdTree.door_db[DoorId])
    )
    return txt

def __code(Node, TheEntry, done_set):
    """Code a node of the command tree in a sequence of nodes from leaf to
    root, parent by parent. As long as the parent is in the list, no goto is
    required. If the parent is implemented already, an explicit goto is 
    implemented.

    RETURNS: list of strings = code for node.
    """
    __comment(txt, Node, TheEntry)
    __label_node(txt, Node)

    # (*) The code of commands of the node
    txt.extend(
        Lng.COMMAND_LIST(Node.command_list)
    )

    # (*) The 'goto parent'.
    if Node.parent not in done_set:
        # As long as the parent is not done, it will be implemented immediately
        # after this node--no goto is required.
        return txt

    elif Node.command_list and Node.command_list[-1].id == E_Cmd.GotoDoorId: 
        # Goto is futile if the last command is an unconditional goto.
        return txt

    else:
        # Append the 'goto parent'
        txt.append("    %s\n" % Lng.GOTO(Node.parent.door_id))
        return txt

def __comment(txt, Node, TheEntry):
    """Comment on the states from where the door is entered.

    RETURNS: String 

    The string contains information about the entries which the node represents.
    In MegaStates it may be possible that an entry representes entries TO 
    multiple different states.
    """
    # 'Node.child_set is None' => leaf node, i.e. entry from other state. 
    # Otherwise: nothing to be done.
    if Node.child_set is not None: return

    transition_id_list = TheEntry.get_transition_id_list(Node.door_id)
    if not transition_id_list: return "\n"

    msg = "".join(
        "(%s from %s) " % (x.target_state_index, x.source_state_index) \
        for x in transition_id_list
    )
    txt.append("    %s" % Lng.COMMENT(msg)[:-1])

def __label_node(Node):
    """The 'label' of a node in the command tree. Note, that depending on child 
    number:

             == 0   => 'outer node' and gotoed from outside 
                    => label REQUIRED.
                    
             == 1   => 'inside node' and slipped in from child 
                    => no label required.
                    
             >= 2   => 'inside node' and gotoed from inside.
                    => label REQUIRED

    NOTE Case '>= 2': the 'goto parent' might be disabled by a 'goto'
         in the command list of a node. Consequently, it is possible that it is
         not gotoed, and therefore its implementation must be made CONDITIONAL. 

    NOTE Case == 0: There is a special case at the global entry into the
         analyzer. Then, no label is required. So, its safe to make it also
         CONDITIONAL.
    """
    if Node.child_set is None:               # leaf node (entered from outside!)
        txt.append(IfDoorIdReferencedLabel(Node.door_id))
    elif len(Node.child_set) >= 2:           # inner node (gotoed by child)
        txt.append(IfDoorIdReferencedLabel(Node.door_id))
