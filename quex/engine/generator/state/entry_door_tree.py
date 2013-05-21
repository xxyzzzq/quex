# (C) 2006-2013 Frank-Rene Schaefer
from quex.engine.analyzer.state.entry_action import *
from quex.blackboard  import E_StateIndices

from collections import defaultdict
from itertools   import islice
from operator    import attrgetter

def do(StateIndex, TransitionActionDB):
    """Better clone the TransitionActionList before calling this function, 
       if the content as it is is till required later.

       Note: 'Door 0' is supposed to be the node without any commands.
             This is used for 'after reload', where the state is entered
             a second time with freshly loaded data.

       It is assumed, that the actions in 'TransitionActionDB' are
       '.categorized', i.e.  the command list are associated with a 'DoorID'.
    """
    candidate_list         = CandidateList(TransitionActionDB)

    door_sub_index_counter = TransitionActionDB.largest_used_door_sub_index + 1
    while 1 + 1 == 2:
        # Get best combination of command lists--those which share the 
        # most and are shared by the most.
        best = candidate_list.pop_best()
        if best is None: break

        # Delete the command commands from the doors which share the 
        # 'best.command_list'.
        for child in best.door_set:
            child.command_list.difference_update(best.command_list)

        new_door_id             = DoorID(StateIndex, door_sub_index_counter)
        door_sub_index_counter += 1
        new_door                = Door(best.command_list, 
                                       ChildList = best.door_set, 
                                       DoorId    = new_door_id)
        candidate_list.enter(new_door)

    print "#candidate_list.no_sharer_list:", [ "%s\n" % x.door_id for x in candidate_list.no_sharer_list ]
    root = Door(None, candidate_list.no_sharer_list, 
                DoorID(StateIndex, 0))

    Door.paternity_log(root, TransitionActionDB)

class Door:
    """A 'Door' is a node in a door tree. A door tree is constructed from 
       a set of command lists, each command list is to be executed upon 
       entry from another state. For example,


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

       The entry from state 'A' happens through door 2 and the entry from state
       'B' happens through door 1. Door 1 and 2 store door 0 as their parent.
       By means of the the '.parent' and '.child_list' members the tree
       structure is maintained. The relation from which state one comes and
       through which door one enters is stored in the global variable
       'Door.transition_id_to_door_id_db', it maps:

                  transition_id ---> door_identifier
    """
    def __init__(self, CommandList, ChildList, DoorId):
        # Only 'Leaf' nodes have the 'related actions', i.e. TA assigned.
        assert isinstance(DoorId, DoorID)
        self.parent       = None  
        self.child_list   = ChildList
        self.command_list = CommandList
        self.__door_id    = DoorId
        print "#DoorId:", DoorId

    @staticmethod
    def paternity_log(tree_root, DEBUG_ADB):
        done_set  = set()
        work_list = [ tree_root ]
        while len(work_list) != 0:
            parent = work_list.pop()
            assert parent.door_id not in done_set, "Recursion should not happen in the door tree!"
            for child in parent.child_list:
                child.parent = parent
            work_list.extend(x for x in parent.child_list)
            
            done_set.add(parent.door_id)

    @property
    def door_id(self):
        return self.__door_id

    def has_commands_other_than_MegaState_Command(self):
        # __dive --> here we have recursion
        for found in (x for x in self.common_command_list if not isinstance(x, MegaState_Command)):
            return True

        for child in self.child_list:
            if child.has_commands_other_than_MegaState_Command(): return True

        return False

    def __hash__(self):
        return hash(self.door_id)

    def __eq__(self, Other):
        return self.door_id == Other.door_id

    def __repr__(self):
        return "Door(id: %s)" % self.door_id
        assert False, "Use 'get_string()'"

    def get_string(self, ActionDB, OnlyFromStateIndexF=False):
        """DoorID_to_TransitionID_DB can be received, for example from the 
           'entry.action_db' object.
        """
        DoorID_to_TransitionID_DB = defaultdict(list)
        #for transition_id, action in ActionDB.iteritems():
        #    DoorID_to_TransitionID_DB[transition_id].append(action.door_id)

        txt = []
        for child in sorted(self.child_list, key=attrgetter("door_id")):
            txt.append("%s\n" % child.get_string(DoorID_to_TransitionID_DB))

        if self.door_id is not None: txt.append("[%s]: " % self.door_id.door_index)
        else:                        txt.append("[None]: ")

        #transition_id_list = DoorID_to_TransitionID_DB[self.door_id]
        #for transition_id in sorted(transition_id_list, key=attrgetter("state_index", "from_state_index")):
        #    if OnlyFromStateIndexF:
        #        txt.append("(%s) " % transition_id.from_state_index)
        #    else:
        #        txt.append("(%s<-%s) " % (transition_id.state_index, transition_id.from_state_index))
        if self.command_list is not None:
            txt.append("\n")
            for action in self.command_list:
                action_str = repr(action)
                action_str = "    " + action_str[:-1].replace("\n", "\n    ") + action_str[-1]
                txt.append(action_str)

        if self.parent is None: txt.append("parent: [None]\n")
        else:                   txt.append("parent: [%s]\n" % repr(self.parent.door_id.door_index))
        return "".join(txt)

class CandidateList(list):
    def __init__(self, TransitionActionDB):
        """Compare the shared command lists between doors in the DoorList.
        Associate each sharing with a 'gain'.
        """
        class SharingInfo:
            def __init__(self, SharedCmdList, DoorSet):
                """SharedCmdList -- List of commands shared by the doors.
                   DoorIdList    -- Ids of the doors which share the commands.
                """
                self.gain         = - SharedCmdList.cost() * len(DoorSet)
                self.command_list = SharedCmdList
                # self.door_id_set  = set(x.door_id for x in DoorSet)
                self.door_set     = DoorSet

            def add_door(self, TheDoor):
                # Update 'gain':  (gain per door: gain / L) * (new number of doors: L + 1)
                L         = (self.door_set)
                self.gain = (self.gain / L) * (L + 1)
                self.door_set.add(TheDoor)

        def iterable(DoorList):
            for i, door_x in enumerate(DoorList):
                for door_y in islice(DoorList, i+1):
                    print "#dydy:", door_x, door_y
                    yield door_x, door_y

        def shared_command_list(DoorX, DoorY):
            return CommandList(cmd for cmd in DoorX.command_list 
                                   if DoorY.command_list.has_action(cmd))

        print "#Begin"
        DoorList = [
             Door(action.command_list, ChildList=[], DoorId=action.door_id)
             for transition_id, action in TransitionActionDB.iteritems()
                if transition_id.from_state_index != E_StateIndices.NONE
        ]
        print "#DoorList:", DoorList
        share_db    = defaultdict(set)
        sharer_list = []
        for x, y in iterable(DoorList):
            cmd_list = shared_command_list(x, y)
            if cmd_list.is_empty(): continue
            share_db[cmd_list].add(x); share_db[cmd_list].add(y)
            sharer_list.append(x);     sharer_list.append(y)
        
        self.no_sharer_list = [ 
            x for x in DoorList if x not in sharer_list 
        ]

        self.extend(
            SharingInfo(cmd_list, door_set)
            for cmd_list, door_set in share_db.iteritems()
        )

        self.sort(key=attrgetter("gain"))

    def pop_best(self):
        if len(self) == 0:
            return None

        best = self.pop()

        self.__delete_references(best.door_set)

        return best

    def enter(self, NewDoor):
        shared_f  = False
        for share_info in self:
            cmd_list = shared_command_list(NewDoor.command_list, 
                                           share_info.command_list)
            if cmd_list.is_empty(): continue
            share_info.add_door(NewDoor)
            shared_f = True

        if not shared_f:
            self.no_sharer_list.append(NewDoor)

        self.sort(key=attrgetter("gain"))
        
    def __delete_references(self, DoneDoorSet):
        """Delete all references to any door in DoorList. 
        """
        i = len(self) - 1
        while i >= 0:
            share_info = self[i]
            share_info.door_id_set.difference_update(DoneDoorSet)
            # A command list that is shared by less than 2, is not shared.
            if len(share_info.door_id_set) == 1:
                self.no_sharer_list.append(share_info.door_set.pop())
                del self[i]
            elif len(share_info.door_id_set) == 0:
                del self[i]
            i -= 1

        return 
    
