"""The 'Door Tree' ____________________________________________________________    

DEFINITION: 
    
    A 'Door' is associated with a specific command list which is executed upon 
    entry into a states. That is, a door from the door's id the command list can
    be concluded and vice versa:

                      DoorID <--> Commands to be executed.

PRINCIPLE:

Several doors into a state may share commands which can be extracted into a
tail. Imagine Door 1 and 2 in the following example:
    
            Door 1:  [ X, Y, Z ]

            Door 2:  [ U, V, Y, Z ]

Both share the Y and Z and the end. So, a common tail can be implemented and
the configuration becomes:
    
            Door 1:  [ X ] ------.
                                 +----> [ Y, Z ]
            Door 2:  [ U, V ] ---'

in which case Y and Z are implemented only once, instead of each time for door
1 and door 2.

_______________________________________________________________________________

PROCEDURE:

A state's entry already determined the unique set of command lists and
associated each command list with a DoorID. Starting from there, a set 
of Door-s can be built which are all connected to the 'root', i.e. the 
final entry into the state.

            Door 1:  [ X, Y, Z ] --------.
            Door 2:  [ U, V, Y, Z ] ------+
            ...                            +----> root
            Door N:  [ P, Q, Z ] ---------'

Now, build a matrix that tells what doors have what tail in common.

                   1   2  ...  N         (Note, only one triangle 
                1                         of the matrix needs to be
                2                         determined; symmetrie!)
               ...       T(i,k)
                N

Let T(i,k) be the common tail of Door 'i' with Door 'k'. Considering
the longest tail of the whole matrix. Then it is save to assume that

       There is no way that more commands can be cut out of 'i' 
       and 'k' then with the given combination. 

Thus, once the combination is done, 'i' and 'k' is done and no longer
subject to combination considerations. The combination results in 
a new door. Let's assume i was 1 and k was 2:

            Door 1:  [ X ] -------.   Door x0
            Door 2:  [ U, V ] -----+--[ Y, Z ]--.
            ...                                  +----> root
            Door N:  [ P, Q, Z ] ---------------'

The new Door x0 is the 'parent' of Door 1 and Door 2. Its parent is root. 
Now, 1 and 2 are done and what remains is Door x0. 

Note, only those doors can combine their 'tails' whose parent is the same.
The parent represents the 'tail' commands. With the current algorithm, though,
all generated nodes have 'root' as their parent. Thus, the requirement that
all candidates share the parent is given.

_______________________________________________________________________________

FUNCTIONS:

    do(): -- Does the optimization. Returns the root door. Iterate over
             tree by each node's child_set.
           
(C) Frank-Rene Schaefer
_______________________________________________________________________________
"""
from   quex.engine.analyzer.door_id_address_label import DoorID, dial_db
from   quex.engine.analyzer.commands.core         import CommandList
import quex.engine.analyzer.commands.shared_tail  as     shared_tail

from quex.blackboard  import E_StateIndices, \
                             E_DoorIdIndex
from quex.engine.tools import pair_combinations

from collections      import defaultdict, namedtuple
from itertools        import islice
from operator         import attrgetter

Door = namedtuple("Door", ("door_id", "command_list", "parent", "child_set"))


class SharedTailCandidateSet(object):
    """A SharedTailCandidateSet is 1:1 associated with a shared tail command list.
    It contains the DoorID-s of doors that share the tail and what indices would
    have to be cut out of the door's command list if the shared tail was to be 
    extracted. All this information is stored in a map:

                           DoorId --> Cut Index List

    The shared tail which is related to the SharedTailCandidateSet is NOT stored here.
    It is stored inside the SharedTailDB as a key.
    """
    __slots__ = ("cut_db", "tail_length")
    def __init__(self, TailLength):
        self.cut_db = {}
        self.tail_length = TailLength

    def add(self, DoorId, CutIndexList):
        """DoorId       -- DoorID to be added.
           CutIndexList -- List of indices to be cut in order to extract
                           the shared tail.
        """
        entry = self.cut_db.get(DoorId)
        if entry is not None:
            assert entry == CutIndexList
            return
        self.cut_db[DoorId] = CutIndexList

    def value(self):
        return len(self.cut_db) * self.tail_length

    def __str__(self):
        txt = [ 
            "    .tail_length: %i;\n" % self.tail_length,
            "    .cut_db: {\n",
        ]
        for door_id, cut_indices in self.cut_db.iteritems():
            txt.append("        %s -> { %s }\n" % (str(door_id), "".join("%i, " % i for i in cut_indices_str)))
        txt.append("    }\n")
        return "".join(txt)


class SharedTailDB:
    """_________________________________________________________________________                     
    Database that allows to combine shared tails of command list sequentially.

       .pop_best() -- Find the best combination of Door-s who can share a 
                      command list tail. 
                   -- Extract the tail from the Door-s' command lists. 
                   -- Generate a new Door with the tail. 
                      + The 'parent' the Door-s' parent (i.e. always '.root'). 
                      + The childs are the Door-s from which the tail has been 
                        extracted.
                   -- Delete the sharing Door-s from the list of candidates.
                   -- Determine sharing relationships of new Door with present
                      candidates.

    The '.pop_best()' function is to be called repeatedly until it returns
    'None'. In that case there are no further candidates for shared tail 
    combinations.
    ____________________________________________________________________________
    MEMBERS:

        .state_index = Index of the state for which the procedure operates.
                       This is required for the generation of new DoorID-s.

        .door_db     = Dictionary containing all Door-s which are opt to 
                       share a command list tail.

                         map:    DoorID --> Door

        .db          = Dictionary holding information about what shared
                       tail (as a tuple) is shared by what Door-s.

                         map:    shared tail --> SharedTailCandidateSet
    ____________________________________________________________________________                     
    """
    __slots__ = ("state_index", "door_id_set", "db")

    def __init__(self, StateIndex, DoorId_CommandList_Iterable):
        self.state_index = StateIndex
        self.root        = Door(dial_db.new_door_id(StateIndex), [], None, set())

        # map: Shared Tail --> SharedTailCandidateSet
        self.db      = {}
        self.door_db = {}
        for door_id, command_list in DoorId_CommandList_Iterable:
            door = Door(door_id, command_list, self.root, set())
            self._enter(door_id, door)

    def pop_best(self):
        """RETURNS: The best candidate for a shared tail extraction. This is, 
                    obviously the candidate with the longest, most shared tail.
        """
        if len(self.db) == 0:
            return None

        best_tail, best_candidate = self._find_best()
        for door_id in best_candidate.cut_db.iterkeys():
            self._remove_door_references(door_id)
        self._new_node(best_tail, best_candidate)

    def _find_best(self):
        """Find the combination that provides the most profit. That is, the
        combination which is shared by the most and has the longest tail.
        """
        best_value     = -1
        best_candidate = None
        best_tail      = tail
        for tail, candidate in self.db.iteritems():
            value = candidate.value()
            if value <= best_value: continue
            best_value     = value
            best_candidate = candidate
            best_tail      = tail

        return best_tail, best_candidate

    def _remove(self, DoorId):
        """Remove all references of DoorId inside the database. That is, the
        related door does no longer act as candidate for further shared-tail
        combinations.
        """
        trash = None
        for tail, candidate in self.db.iteritems():
            if candidate.remove_door_reference(DoorId) == True: continue
            # candidate is now empty --> no shared tail
            if trash is None: trash = [ tail ]
            else:             trash.append(tail)

        for tail in trash:
            del self.db[tail]

        del self.door_db[door_id]

    def _new_node(self, Tail, Candidate):
        """A Tail has been identified as being shared and is now to be extracted
        from the sharing doors. Example: 'Y, Z' is a shared tail of doord 1 and 2:
        
                        Door 1:  [ X, Y, Z ] --------.
                        Door 2:  [ U, V, Y, Z ] ------+
                        ...                            +----> root
                        Door N:  [ P, Q, Z ] ---------'

        The 'Y, Z' is extracted into a new door, and door 1 and 2 need to goto the
        new door after the end of their pruned tail.

                        Door 1:  [ X ] -------.   new Door 
                        Door 2:  [ U, V ] -----+--[ Y, Z ]--.
                        ...                                  +----> root
                        Door N:  [ P, Q, Z ] ---------------'

        PROCEDURE: (1) Generate DoorID for the new node.
                   (2) Prune the command lists of the sharing doors.
                   (3) Set their 'parent' to the new node's DoorID.
                   (4) Enter new node with (DoorID, Tail) into the door database.
        """
        new_door_id = dial_db.new_door_id(self.state_index)
        # All new Door-s relate to '.root'
        new_door    = Door(new_door_id, CommandList, self.root, child_set)

        for door_id, cut_index_list in Candidate.cut_db.iteritems():
            door = self.door_db[door_id]
            for index in reversed(cut_index_list):
                del door.command_list[index]

            # Doors that have been combined, did so with the 'longest' possible
            # tail. Thus, they are done!
            self._remove(door_id)
            # -- '.parent' is only set to new doors.
            # -- all new doors relate to '.root'.
            # => The parent of all considered Door-s in the database is '.root'
            assert door.parent == self.root
            door.parent = new_door
            self.root.child_set.remove(door)

        self.root.child_set.add(new_door)

        child_set = set(Canditate.iterkeys())

        self._enter(new_door_id, new_door)

    def _enter(self, NewDoorId, NewDoor):
        """(1) Determine the shared tail with any other available door.
           (2) Enter the new Door in door_db.
        """

        for door_id, door in self.door_db.iteritems():
            tail,   \
            x_cut_indices, y_cut_indices = shared_tail.get(NewDoor.command_list, 
                                                           door.command_list)
            if tail is None: continue

            self._register_shared_tail(tail, NewDoorId, door_id, 
                                       x_cut_indices, y_cut_indices)

        self.door_db[NewDoorId] = NewDoor

    def _register_shared_tail(self, SharedTail, DoorId_A, DoorId_B, CutIndicesA, CutIndicesB):
        """If (x0, x1, ...  xN) is a shared tail, then (x1, ... xN) is also 
           a shared tail. Add all tails to the database.
        """
        tail = SharedTail
        for i in xrange(len(tail)):
            entry = self.db.get(tail)
            if entry is None:
                entry = SharedTailCandidateSet(len(tail))
                self.db[tail] = entry
            entry.add(DoorId_A, CutIndicesA[i:])
            entry.add(DoorId_B, CutIndicesB[i:])
            tail = tail[1:]

    def get_string(self, CommandAliasDb):
        txt = [
            ".state_index:    %i;\n" % self.state_index,
            ".root (door_id): %s;\n" % str(self.root.door_id),
            ".door_db.keys(): %s;\n" % "".join("%s, " % str(door_id) for door_id in self.door_db.iterkeys()),
            ".shared_tails: {\n"
        ]
        
        for shared_tail, candidate_set in self.db.iteritems():
            txt.append("  (%s) -> {\n" % "".join("%s;" % CommandAliasDb[cmd] for cmd in shared_tail))
            txt.append(str(candidate_set))
        txt.append("  }\n")

        # map: Shared Tail --> SharedTailCandidateSet
        self.db      = {}
        txt.append("}\n")
        return "".join(txt)


def do(StateIndex, DoorId_CommandList_Iterable):
    """StateIndex -- Index of state for which one operates.
                     (needed for new DoorID generation)
       
       DoorId_CommandList_Iterable -- Iterable over pairs of 

                     (DoorID, command lists)

    NOTE: The command lists are MODIFIED during the process of finding
          a command tree!
    """
    shared_tail_db = SharedTailDB(StateIndex, DoorId_CommandList_Iterable)

    while shared_tail_db.pop_best():
        pass

    return shared_tail_db.root

def get_string(DoorTreeRoot):
    """ActionDB can be received, for example from the 'entry' object.
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

    if self.door_id is not None: 
        txt.append("[%s:%s]: " % (self.door_id.state_index, self.door_id.door_index))
    else:                        
        txt.append("[None]: ")

    if ActionDB is not None:
        transition_id_list = door_id_to_transition_id_list(self.door_id, ActionDB)
       
        for transition_id in sorted(transition_id_list, key=attrgetter("target_state_index", "source_state_index")):
            if OnlyFromStateIndexF:
                txt.append("(%s) " % transition_id.source_state_index)
            else:
                txt.append("(%s<-%s) " % (transition_id.target_state_index, transition_id.source_state_index))

    if self.command_list is not None:
        txt.append("\n")
        for cmd in self.command_list:
            cmd_str = str(cmd)
            cmd_str = "    " + cmd_str.replace("\n", "\n    ") + "\n"
            txt.append(cmd_str)
        if len(txt[-1]) == 0 or txt[-1][-1] != "\n":
            txt.append("\n")
    else:
        txt.append("\n")

    if self.parent is None: txt.append("    parent: [None]\n")
    else:                   txt.append("    parent: [%s:%s]\n" % \
                                       (str(self.parent.door_id.state_index), 
                                        str(self.parent.door_id.door_index)))
    return "".join(txt)

