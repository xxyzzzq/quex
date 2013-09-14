"""The Door Tree ______________________________________________________________    

At code generation time, Door-s are organized in a tree structure.  The 'door
tree' tries to avoid double definition of commands of if they appear the same
in multiple doors.

Example:

      From State A:                      From State B:
    
      last_acceptance = 12;              last_acceptance = 12;
      position[0]     = input_p - 2;     position[0] = input_p - 2;
      position[1]     = input_p;         position[1] = input_p - 1;

In this case, the entry from A and B have the following commands in common:

                  last_acceptance = 12;
                  position[0]     = input_p - 2;

The following door tree can be constructed:

        Door 2:                        Door 1:     
        position[1] = input_p;         position[1] = input_p - 1;
        goto Door 0;                   goto Door 0;
        
        
                         Door 0:
                         last_acceptance = 12;
                         position[0]     = input_p - 2;
                         (...  to transition map ... )

The entry from state 'A' happens through door 2 and the entry from state 'B'
happens through door 1.  Door 1 and 2 store door 0 as their parent. It implements
what their shared CommandList. 

The structure of the tree is maintained by the '.parent' and '.child_set'
members of Door object.
_______________________________________________________________________________
(C) Frank-Rene Schaefer
"""
from quex.engine.analyzer.state.entry_action import *
from quex.blackboard  import E_StateIndices, \
                             E_DoorIdIndex

from collections      import defaultdict
from itertools        import islice
from operator         import attrgetter

def do(StateIndex, TransitionActionDB):
    """Better clone the TransitionActionList before calling this function, 
       if the content as it is is till required later.

       Note: 'Door 0' is supposed to be the node without any commands.
             This is used for 'after reload', where the state is entered
             a second time with freshly loaded data.

       It is assumed, that the actions in 'TransitionActionDB' are
       '.categorized', i.e.  the command list are associated with a 'DoorID'.
    """
    root = Door(CommandList(), None, None, DoorID(StateIndex, E_DoorIdIndex.EMPTY))

    # Multiple transactions may share the same DoorID. Filter.
    door_set = set()
    done_db  = {}
    for action in TransitionActionDB.itervalues():
        if action.door_id in done_db: 
            # If two action share the same DoorID, their actions must be the same
            assert action == done_db[action.door_id]
            continue

        done_db[action.door_id] = action

        assert action.door_id is not None # '.categorize()' must have been called before!
        # Begin: All doors relate to transitions for other states. They are 
        #        'childs' of root. Root is the door without command lists.
        #
        #                       .-- DoorA: c2, c4, c7, c9
        #          root: <> ----+-- DoorB: c0, c4, c5, c9
        #                       +-- DoorC: c0, c3, c7, c9
        #                       '-- DoorD: c1, c7, c9
        #    
        # A parent/child relationship is maintained by mentioning the child in the 
        # '.child_set' of the parent and with the '.parent' member of every child
        # pointing to the parent.
        door_set.add(Door(action.command_list, Parent=root, ChildSet=None, DoorId=action.door_id))

    root.child_set = door_set

    # Possible shared command list sets -- organized by the shared command list
    #
    #          c4, c9      shared by (DoorA, DoorB, DoorD) 
    #          c0, c4, c9  shared by (DoorB, DoorC)
    #          c7, c9      shared by (DoorC, DoorD)
    #
    # (For doors to share they must have the same parent)
    candidate_list = CandidateList(door_set)

    door_sub_index_counter = TransitionActionDB.largest_used_door_sub_index 
    while 1 + 1 == 2:
        # Get best combination of command lists--those which share the 
        # most and are shared by the most.
        best = candidate_list.pop_best_combination()
        # Example: 
        #             best = c4, c9 shared by (DoorA, DoorB, DoorD)
        if best is None: break

        # (1) Generate a new branch in the tree.
        #
        # The branch is a 'Door' object with the shared command list.  Its
        # parent is the common parent of the sharing doors; its childs are the
        # sharing doors.
        door_sub_index_counter += 1
        new_door = Door(CmdList  = best.command_list, 
                        ChildSet = best.door_set, 
                        Parent   = best.parent,
                        DoorId   = DoorID(StateIndex, door_sub_index_counter))

        # -- Remove child branches from direct parent. They are now parented
        #    by 'new_node' which is a child of parent.
        assert best.parent is not None # The root node is never combined!
        new_door.parent.child_set.difference_update(new_door.child_set)
        # -- Inform parent about the new_door being the direct child
        new_door.parent.child_set.add(new_door)

        # -- Shared commands must be deleted from childs. They are implemented
        #    in new 'new_door.command_list'.
        for child in new_door.child_set:
            child.command_list.difference_update(new_door.command_list)
            # Set new door as parent of childs
            child.parent = new_door
         
        # Resulting tree with 'New' door:
        #                                             .-- DoorA: c2, c7
        #        root --+-- New:   c4, c9 ------------+-- DoorB: c0, c5
        #               |                             '-- DoorD: c1, c7
        #               |
        #               '-- DoorC: c0, c3, c7, c9

        # (2) Update the list of possible combinations
        #
        # -- The children's command lists have been modified. Thus, any
        #    possible combination which includes them is invalid.
        candidate_list.delete_references(new_door.child_set)

        # -- Enter the modified doors into candidate list, if the share 
        #    something.
        candidate_list.enter_door_set_of_new_parent(new_door.child_set)
        # -- Enter the new door as a possible 'sharer' into the candidate list.
        candidate_list.enter_door(new_door)
        
    # It is conceivable, that an empty 'root' had only one child. In that case, the
    # child may play the role of 'root'.
    #if len(root.child_set) == 1 and root.command_list.is_empty(): 
    #    root = root.child_set.pop()
    #    root.parent = None
    return root

def find(root, DoorId):
    """Searches in the Door-Tree given by its 'root' for a node with 'DoorId'.
    RETURNS: None - of no such node was found.
             node - which is the node with '.door_id == DoorId'.
    """
    work_list = [root]
    done_set  = set()
    while len(work_list) != 0:
        candidate = work_list.pop()
        print "#dd:", DoorId, candidate.door_id
        print "#childset:", candidate.child_set
        if candidate.door_id == DoorId:
            return candidate
        assert candidate.door_id not in done_set
        done_set.add(candidate.door_id)
        if candidate.child_set is not None:
            work_list.extend(candidate.child_set)
    return None

class DoorCombination:
    def __init__(self, SharedCmdList, Parent, DoorSet):
        """SharedCmdList -- List of commands shared by the doors.
           DoorIdList    -- Ids of the doors which share the commands.
        """
        assert isinstance(SharedCmdList, CommandList)
        assert isinstance(DoorSet, set)
        assert len(DoorSet) >= 2
        assert Parent is not None  # Root shall never be part of a combination!

        self.command_list = SharedCmdList
        self.door_set     = DoorSet
        # Command list is implemented once, instead of 'DoorN' times.
        # => gain = cost(command_list) * (N - 1)
        self.parent       = Parent

    @property
    def gain(self):
        return float(self.command_list.cost() * (len(self.door_set) - 1))

class Door:
    """Upon entry into a state CommandList-s wait to be executed, depending on
       the original state or even the trigger. Each distinct CommandList is
       associated with a 'Door' of the 'Entry' into the 'AnalyzerState'.
   """
    def __init__(self, CmdList, Parent, ChildSet, DoorId):
        assert isinstance(CmdList, CommandList)
        assert (ChildSet is None) or isinstance(ChildSet, set)
        assert (Parent is None)   or isinstance(Parent, Door)
        assert isinstance(DoorId, DoorID)
        self.parent       = Parent  
        self.child_set    = ChildSet
        self.command_list = CmdList
        self.__door_id    = DoorId

    @staticmethod
    def paternity_log(tree_root, TransitionActionDB):
        """For each node with a non-empty child_set, assign the childs
           its parent. 

           Re-assign door-indices which have been generated. This is only
           for beauty. The goal is to have a cohesive set of numbers as
           door indices
        """
        done_set  = set()
        work_list = [ tree_root ]

        # Any door_index > door_index_counter_base has been generated.
        door_index_counter_base = TransitionActionDB.largest_used_door_sub_index
        door_index_counter      = door_index_counter_base + 1
        while len(work_list) != 0:
            parent = work_list.pop()
            #if parent.door_id.door_index > door_index_counter_base:
                #parent.door_id.set_door_index(door_index_counter)
                #door_index_counter += 1
            considered_child_list = [x for x in parent.child_set if x not in done_set]
            for child in sorted(considered_child_list):
                child.parent = parent
            work_list.extend(considered_child_list)
            
            done_set.add(parent.door_id)

    @property
    def door_id(self):
        return self.__door_id

    def __hash__(self):
        return hash(self.door_id)

    def __eq__(self, Other):
        return self.door_id == Other.door_id

    def __repr__(self):
        return "Door(id: %s)" % self.door_id.__class__
        assert False, "Use 'get_string()'"

    def get_string(self, ActionDB=None, OnlyFromStateIndexF=False):
        """ActionDB can be received, for example from the 'entry.action_db' object.
           If it is 'None', then no transition-id information is printed.
        """
        def door_id_to_transition_id_list(DoorId, ActionDB):
            if ActionDB is None:
                return None
            return [
                transition_id for transition_id, action in ActionDB.iteritems()
                              if action.door_id == DoorId
            ]

        txt = []
        if self.child_set is not None:
            def sort_key(X, ActionDB):
                return (door_id_to_transition_id_list(X.door_id, ActionDB), X)
                    
            for child in sorted(self.child_set, key=lambda x: sort_key(x, ActionDB)):
                txt.append("%s\n" % child.get_string(ActionDB))

        if self.door_id is not None: txt.append("[%s:%s]: " % (self.door_id.state_index, self.door_id.door_index))
        else:                        txt.append("[None]: ")

        if ActionDB is not None:
            transition_id_list = door_id_to_transition_id_list(self.door_id, ActionDB)
           
            for transition_id in sorted(transition_id_list, key=attrgetter("target_state_index", "source_state_index")):
                if OnlyFromStateIndexF:
                    txt.append("(%s) " % transition_id.source_state_index)
                else:
                    txt.append("(%s<-%s) " % (transition_id.target_state_index, transition_id.source_state_index))

        if self.command_list is not None:
            txt.append("\n")
            for action in self.command_list:
                action_str = repr(action)
                action_str = "    " + action_str[:-1].replace("\n", "\n    ") + action_str[-1]
                txt.append(action_str)
        else:
            txt.append("\n")

        if self.parent is None: txt.append("parent: [None]\n")
        else:                   txt.append("parent: [%s]\n" % repr(self.parent.door_id.door_index))
        return "".join(txt)

class CandidateList:
    def __init__(self, DoorSet):
        """Compare the shared command lists between doors in the DoorList.
           Associate each sharing with a 'gain'.
        """
        shared_db, sharing_door_set = self.__find_sharings(DoorSet)

        self.possible_combination_list = shared_db.values()
        # A door which does not share yet will never share, because no new
        # commands will appear. Thus, the set of doors which are available
        # for combination is defined by the set of sharing doors. 
        # 
        # The rest of the doors are setup by their 'parent/child' relation
        # ship. They have their place in the door tree already.
        self.available_door_set        = sharing_door_set

    def __find_sharings(self, DoorSet):
        """Enter a set of doors into the database. This function finds shared
           commands in the command list.

           RETURNS:  [0] -- shared_db, i.e. a mapping

                            CommandList --> DoorCombination

                     [1] -- sharing_door_set

        """
        shared_db        = {}
        sharing_door_set = set()
        for x, y in pair_combinations(DoorSet):
            assert x.parent == y.parent 
            cmd_list = CommandList.get_shared_tail(x.command_list, y.command_list)
            if cmd_list.is_empty(): continue
            entry    = shared_db.get(cmd_list)
            if entry is None:
                shared_db[cmd_list] = DoorCombination(cmd_list, Parent=x.parent, DoorSet=set([x, y]))
            else:
                entry.door_set.add(x)
                entry.door_set.add(y)
            sharing_door_set.add(x)
            sharing_door_set.add(y)

        return shared_db, sharing_door_set

    def pop_best_combination(self):
        """Pop the best possible 'combination' of command lists of doors, 
           i.e. the combination which brings the most of a gain.
        """
        best     = None
        best_i   = None
        max_gain = 0     # No negative gain will ever be accepted!
        for i, door_combination in enumerate(self.possible_combination_list):
            if door_combination.gain <= max_gain: continue
            best     = door_combination
            best_i   = i
            max_gain = best.gain

        if best is None:
            return None

        del self.possible_combination_list[best_i]

        return best

    def enter_door_set_of_new_parent(self, DoorSet):
        """Assume: All doors in DoorSet have the same (new) parent. The 
           parent is not yet present in the database. Therefore, no
           shared command lists can appear with other doors from 
           'available_door_set'.
        """
        shared_db, sharing_door_set = self.__find_sharings(DoorSet)
        self.possible_combination_list.extend(shared_db.itervalues())
        self.available_door_set.update(sharing_door_set)

    def enter_door(self, NewDoor):
        """Enter a new door as a candidate into the data base. For this, it
           possible combinations with other doors need to be considered.
        """
        shared_f     = False
        command_list = NewDoor.command_list
        for door in self.available_door_set:
            if door.parent != NewDoor.parent: continue
            cmd_list = CommandList.get_shared_tail(door.command_list, command_list)
            if cmd_list.is_empty(): continue
            shared_f = True
            # It is impossible that exact the same command list appears in another
            # door combination with the same parent. Otherwise, it would have been
            # combined into the 'best' door combination before.
            dc = DoorCombination(cmd_list, door.parent, set([door, NewDoor]))
            self.possible_combination_list.append(dc)

        if shared_f:
            self.available_door_set.add(NewDoor)
        
    def delete_references(self, DoneDoorSet):
        """Delete all references to any door in DoorList. 
        """
        i = len(self.possible_combination_list) - 1
        while i >= 0:
            candidate = self.possible_combination_list[i]
            candidate.door_set.difference_update(DoneDoorSet)
            # A command list that is shared by less than 2, is not shared.
            # => it is no longer a candidate.
            if len(candidate.door_set) <= 1:
                del self.possible_combination_list[i]
            i -= 1

        return 
    
