from collections     import defaultdict, namedtuple
from quex.blackboard import E_StateIndices, E_PreContextIDs, E_AcceptanceIDs, E_PostContextIDs, E_TransitionN
from operator        import attrgetter
from itertools       import ifilter

class BASE_Entry(object):
    def uniform_doors_f(self):
        assert False, "This function needs to be overloaded for '%s'" % self.__class__.__name__
    def has_special_door_from_state(self, StateIndex):
        """Require derived classes to be more specific, if necessary."""
        return not self.uniform_doors_f()

class EntryAction(object):
    @staticmethod
    def type_id():      assert False
    def priority(self): assert False

# EntryAction_StoreInputPosition: 
#
# Storing the input position is actually dependent on the pre_context_id, if 
# there is one. The pre_context_id is left out for the following reasons:
#
# -- Testing the pre_context_id is not necessary.
#    If a pre-contexted acceptance is reach where the pre-context is required
#    two things can happen: 
#    (i) Pre-context-id is not fulfilled, then no input position needs to 
#        be restored. Storing does no harm.
#    (ii) Pre-context-id is fulfilled, then the position is restored. 
#
# -- Avoiding overhead for pre_context_id test.
#    In case (i) cost = test + jump, (ii) cost = test + assign + jump. Without
#    test (i) cost = assign, (ii) cost = storage. Assume cost for test <= assign.
#    Thus not testing is cheaper.
#
# -- In the process of register economization, some post contexts may use the
#    same position register. The actions which can be combined then can be 
#    easily detected, if no pre-context is considered.
class EntryAction_StoreInputPosition(object):
    __slots__ = ["pre_context_id", "position_register", "offset"]
    def __init__(self, PreContextID, PositionRegister, Offset):
        self.pre_context_id    = PreContextID
        self.position_register = PositionRegister
        self.offset            = Offset

    # Require 'type_id' and 'priority' for sorting of entry actions.
    @staticmethod
    def type_id():      return 0
    def priority(self): return - self.position_register

    # Require '__hash__' and '__eq__' to be element of a set.
    def __hash__(self):
        return 1
    def __eq__(self, Other):
        if not isinstance(Other, EntryAction_StoreInputPosition): return False
        return     self.pre_context_id    == Other.pre_context_id \
               and self.position_register == Other.position_register \
               and self.offset            == Other.offset           

# EntryAction_Accepter:
# 
# In this case the pre-context-id is essential. We cannot accept a pattern if
# its pre-context is not fulfilled.
EntryAction_AccepterElement = namedtuple("EntryAction_AccepterElement", ("pre_context_id", "pattern_id"))
class EntryAction_Accepter(object):
    __slots__ = ["__list"]
    def __init__(self):
        self.__list = []
    
    def add(self, PreContextID, PatternID):
        self.__list.append(EntryAction_AccepterElement(PreContextID, PatternID))

    def insert_front(self, PreContextID, PatternID):
        self.__list.insert(0, EntryAction_AccepterElement(PreContextID, PatternID))

    # Require 'type_id' and 'priority' for sorting of entry actions.
    @staticmethod
    def type_id():      return 1
    def priority(self): return len(self.__list)

    # Require '__hash__' and '__eq__' to be element of a set.
    def __hash__(self):
        return 1
    def __eq__(self, Other):
        if not isinstance(Other, EntryAction_Accepter): return False
        return self.__list == Other.__list

    def __iter__(self):
        for x in self.__list:
            yield x

    def __repr__(self):
        return "".join(["pre(%s) --> accept(%s)\n" % (element.pre_context_id, element.pattern_id) \
                       for element in self.__list])


class Entry(BASE_Entry):
    """An entry has potentially the following tasks:
    
          (1) Storing information about positioning represented by objects 
              of type 'EntryAction_StoreInputPosition'.

          (2) Storing information about an acceptance. represented by objects
              of type 'EntryAction_StoreInputPosition'.
              
       Entry actions are relative from which state it is entered. Thus, an 
       object of this class contains a dictionary that maps:

                 from_state_index  --> list of entry actions

    """
    __slots__ = ("__uniform_doors_f", "__doors_db")

    def __init__(self, FromStateIndexList):
        # map:  (from_state_index) --> list of actions to be taken if state is entered 
        #                              'from_state_index' for a given pre-context.
        if len(FromStateIndexList) == 0:
            FromStateIndexList = [ E_StateIndices.NONE ]
        self.__doors_db = dict([ (i, set()) for i in FromStateIndexList ])

        # Are the actions for all doors the same?
        self.__uniform_doors_f = None 

    def doors_accept(self, FromStateIndex, PathTraceList):
        """At entry via 'FromStateIndex' implement an acceptance pattern that 
           is determined via 'PathTraceList'. This function is called upon the
           detection of a state that restores acceptance. The previous state 
           must be of uniform acceptance (does not restore). At the entry of 
           this function we implement the acceptance pattern of the previous
           state.
        """
        # Construct the Accepter from PathTraceList
        accepter = EntryAction_Accepter()
        for path_trace in PathTraceList:
            accepter.add(path_trace.pre_context_id, path_trace.pattern_id)

        self.__doors_db[FromStateIndex].add(accepter)

    def doors_accepter_add_front(self, PreContextID, PatternID):
        """Add an acceptance at the top of each accepter at every door. If there
           is no accepter in a door it is created.
        """
        for door in self.__doors_db.itervalues():
            # Catch the accepter, if there is already one, of not create one.
            accepter = None
            for element in door:
                if isinstance(element, EntryAction_Accepter): 
                    accepter = element
                    break
            if accepter is None: 
                accepter = EntryAction_Accepter()
                door.add(accepter)
            accepter.insert_front(PreContextID, PatternID)

    def doors_store(self, FromStateIndex, PreContextID, PositionRegister, Offset):
        # Add 'store input position' to specific door. See 'EntryAction_StoreInputPosition'
        # comment for the reason why we do not store pre-context-id.
        entry = EntryAction_StoreInputPosition(PreContextID, PositionRegister, Offset)
        self.__doors_db[FromStateIndex].add(entry)

    def door_number(self):
        total_size = len(self.__doors_db)
        # Note, that total_size can be '0' in the 'independent_of_source_state' case
        if self.__uniform_doors_f: return min(1, total_size)
        else:                      return total_size

    def categorized_doors(self):
        class Door:
            """A Door consists a list of actions which are performed upon entry to
               the state from a specific source state.
            """
            def __init__(self, FromStateIndex, ActionList):
                self.from_state_index = FromStateIndex
                self.action_list      = ActionList

            # Make Door usable for dictionary and set
            def __hash__(self): return self.from_state_index
            def __eq__(self):   return self.from_state_index

        class Group:
            """A Group is a set of doors that share some common actions.
               The set of common actions may very well be empty.
            """
            id_counter = 0
            door_db    = {}
            def __init__(self, ParentID, DoorList):
                self.parent_id   = ParentID
                self.identifier  = Group.id_counter
                Group.id_counter += 1

                # Actions that are done by every door in the group.
                self.common_action_list = self.get_common_action_list(DoorList)

                # Let the group do the common action, take them out of the doors.
                self.extract_common_action_list(DoorList, self.common_action_list)

                # Differentiate between doors that are completely implemented by
                # what this group and its parent do, and those doors that need further
                # consideration.
                self.door_list         = []  # Doors implemented by this group
                self.pending_door_list = []  # Doors that need further consideration
                for door in DoorList:
                    if len(door.action_list) == 0: 
                        self.door_list.append(door.from_state_index)
                        Group.door_db[door.from_state_index] = self.identifier
                    else:
                        self.pending_door_list.append(door)

                self.child_list  = []

            def extract_common_actions(self, DoorSet):
                DoorSetSize = len(DoorSet)
                counter_db = defaultdict(int)
                for door in DoorSet:
                    for action in door:
                        counter_db[action] += 1

                # Get set of actions which are in all doors
                common_action_set = [ action for action, count in counter_db.iteritems() if count == DoorSetN ]
                for door in DoorSet:
                    for action in common_action_set:
                        door.remove(action)
                return

            def get_common_action_list(self, DoorList):
                """RETURNS: List of actions that appear in all doors."""
                L          = len(DoorList)
                counter_db = defaultdict(int)
                for door in DoorSet:
                    for action in door:
                        counter_db[action] += 1

                # Return all actions that 
                return [ action for action, count in counter_db.iteritems() if count == L ]

            def __repr__(self):
                txt = ["[%i]" % self.__id]
                for child in self.child_list:
                    txt.append(repr(child))

                for door in sorted(self.door_set, key=attrgetter("from_state_index")):
                    txt.append("%i:\n" % door.from_state_index)
                
                txt.append("common:\n")
                for action in self.action_list):
                    txt.append("    %s\n" % action)

                txt.append("    -> %i" % self.parent_id)
                return "".join(txt)

        def get_most_common_action(DoorSet):
            counter_db = defaultdict(int)
            for door in DoorSet:
                for action in door:
                    counter_db[action].append(door)

            return max(counter_db.iteritems(), key=itemgetter(1))[0]

        root = Group([ Door(from_state_index, deepcopy(door)) \
                       for from_state_index, door in self.__doors_db.iteritems()])
        work_list = [ root ]
        while len(work_list) != 0:
            # Consider the group with the most doors
            work_list.sort(key=lambda group: len(group.door_set))

            group = work_list[-1]

            # Find the action most worthy to be considered 'common'
            common_door_set, remainder_door_set = get_most_common_action(group.door_set)

            # If there was no commonality, then the group is done.
            if common_door_set.is_empty(): work_list.remove(group)

            # Split 'group' into common and remainder.
            # -- old group: take out remainder_door_set.
            group.remove_uncommon_doors(common_door_set)
            # -- new group: create new group from remainder_door_set.
            remainder = Group(group.identifier, remainder_door_set)
            group.child_list.append(remainder)
            work_list.append(remainder)

        return root

    def get_accepter(self):
        """Returns information about the acceptance sequence. Lines that are dominated
           by the unconditional pre-context are filtered out. Returns pairs of

                          (pre_context_id, acceptance_id)
        """
        assert False, "Accepters are 'per-door' objects"
        for door in self.__doors_db.itervalues():
            acceptance_actions = [action for action in door if isinstance(action, EntryAction_Accepter)]
            result.update(acceptance_actions)

        result = list(result)
        result.sort(key=attrgetter("acceptance_id"))
        return result

    def size_of_accepter(self):
        """Count the number of difference acceptance ids."""
        assert False, "Accepters are 'per-door' objects"
        db = set()
        for door in self.__doors_db.itervalues():
            for action in door:
                if not isinstance(action, EntryAction_Accepter): continue
                db.add(action.acceptance_id)
        return len(db)

    def has_accepter(self):
        for door in self.__doors_db.itervalues():
            for action in door:
                if isinstance(action, EntryAction_Accepter): return True
        return False

    def get_positioner_db(self):
        """RETURNS: PositionDB
        
           where PositionDB maps:
        
                   from_state_index  -->   Positioner
 
           where Positioner is a list of actions to be taken when the state is entered
           from the given 'from_state_index'.
        """
        return self.__doors_db

    def __hash__(self):
        result = 0
        for action_set in self.__doors_db.itervalues():
            result += len(action_set)
        return result

    def __eq__(self, Other):
        if len(self.__doors_db) != len(Other.__doors_db): 
            return False
        for from_state_index, action_list in self.__doors_db.iteritems():
            other_action_list = Other.__doors_db.get(from_state_index)
            if other_action_list is None: return False
            if action_list != other_action_list: return False
        return True

    def is_equal(self, Other):
        # Maybe, we can delete this ...
        return self.__eq__(self, Other)

    def uniform_doors_f(self): 
        return self.__uniform_doors_f

    def get_uniform_door_prototype(self): 
        if not self.__uniform_doors_f: return None
        return self.__doors_db.itervalues().next()

    def has_special_door_from_state(self, StateIndex):
        """Determines whether the state has a special entry from state 'StateIndex'.
           RETURNS: False -- if entry is not at all source state dependent.
                          -- if there is no single door for StateIndex to this entry.
                          -- there is one or less door for the given StateIndex.
                    True  -- If there is an entry that depends on StateIndex in exclusion
                             of others.
        """
        if   self.__uniform_doors_f:    return False
        elif len(self.__doors_db) <= 1: return False
        return self.__doors_db.has_key(StateIndex)

    def finish(self, PositionRegisterMap):
        """Once the whole state machine is analyzed and positioner and accepters
           are set, the entry can be 'finished'. That means that some simplifications
           may be accomplished:

           (1) If a position for a post-context is stored in the unconditional
               case, then all pre-contexted position storages of the same post-
               context are superfluous.

           (2) If the entry into the state behaves the same for all 'from'
               states then the entry is independent_of_source_state.
        
           At state entry the positioning might differ dependent on the the
           state from which it is entered. If the positioning is the same for
           each source state, then the positioning can be unified.

           A unified entry is coded as 'ALL' --> common positioning.
        """
        if len(self.__doors_db) == 0: 
            self.__uniform_doors_f = True
            return

        # (*) Some post-contexts may use the same position register. Those have
        #     been identified in PositionRegisterMap. Do the replacement.
        for from_state_index, door in self.__doors_db.items():
            if len(door) == 0: continue
            new_door = set()
            for action in door:
                if not isinstance(action, EntryAction_StoreInputPosition):
                    new_door.add(action)
                else:
                    register_index = PositionRegisterMap[action.position_register]
                    new_door.add(EntryAction_StoreInputPosition(action.pre_context_id, register_index, action.offset))
            self.__doors_db[from_state_index] = new_door

        # (*) If a door stores the input position in register unconditionally,
        #     then all other conditions concerning the storage in that register
        #     are nonessential.
        for door in self.__doors_db.itervalues():
            for action in list(x for x in door \
                               if     isinstance(x, EntryAction_StoreInputPosition) \
                                  and x.pre_context_id == E_PreContextIDs.NONE):
                for x in list(x for x in door \
                             if isinstance(x, EntryAction_StoreInputPosition)):
                    if x.position_register == action.position_register and x.pre_context_id != E_PreContextIDs.NONE:
                        door.remove(x)

        # (*) Check whether state entries are independent_of_source_state
        self.__uniform_doors_f = True
        iterable               = self.__doors_db.itervalues()
        prototype              = iterable.next()
        for dummy in ifilter(lambda x: x != prototype, iterable):
            self.__uniform_doors_f = False
            return
        return 

    def __repr__(self):
        def get_accepters(AccepterList):
            if len(AccepterList) == 0: return []

            prototype = AccepterList[0]
            txt    = []
            if_str = "if     "
            for action in prototype:
                if action.pre_context_id != E_PreContextIDs.NONE:
                    txt.append("%s %s: " % (if_str, repr_pre_context_id(action.pre_context_id)))
                else:
                    if if_str == "else if": txt.append("else: ")
                txt.append("last_acceptance = %s\n" % repr_acceptance_id(action.pattern_id))
                if_str = "else if"
            return txt

        def get_storers(StorerList):
            txt = []
            for action in sorted(StorerList, key=attrgetter("position_register")):
                if action.pre_context_id != E_PreContextIDs.NONE:
                    txt.append("if '%s': " % repr_pre_context_id(action.pre_context_id))
                if action.offset == 0:
                    txt.append("%s = input_p;\n" % repr_position_register(action.position_register))
                else:
                    txt.append("%s = input_p - %i;\n" % (repr_position_register(action.position_register), 
                                                          action.offset))
            return txt

        result = []
        for from_state_index, door in self.__doors_db.iteritems():
            accept_action_list = []
            store_action_list  = []
            for action in door:
                if isinstance(action, EntryAction_StoreInputPosition): 
                    store_action_list.append(action)
                else:
                    accept_action_list.append(action)

            result.append("    .from %s:" % repr(from_state_index).replace("L", ""))
            a_txt = get_accepters(accept_action_list)
            s_txt = get_storers(store_action_list)
            content = "".join(a_txt + s_txt)
            if len(content) == 0:
                # Simply new line
                content = "\n"
            elif content.count("\n") == 1:
                # Append to same line
                content = " " + content
            else:
                # Indent properly
                content = "\n        " + content[:-1].replace("\n", "\n        ") + content[-1]
            result.append(content)


        if len(result) == 0: return ""
        return "".join(result)

class EntryBackwardInputPositionDetection(BASE_Entry):
    """There is not much more to say then: 

       Acceptance State 
       => then we found the input position => return immediately.

       Non-Acceptance State
       => proceed with the state transitions (do nothing here)

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__terminated_f")

    def __init__(self, OriginList, StateMachineID):
        self.__terminated_f = False
        for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
            self.__terminated_f = True
            return

    def uniform_doors_f(self):
        # There is no difference from which state we enter
        return True

    def __hash__(self):
        return hash(int(self.__terminated_f))

    def __eq__(self, Other):
        return self.__terminated_f == Other.__terminated_f 

    def is_equal(self, Other):
        return self.__eq__(Other)

    @property
    def terminated_f(self): return self.__terminated_f

    def __repr__(self):
        if self.__terminated_f: return "    Terminated\n"
        else:                   return ""

class EntryBackward(BASE_Entry):
    """(*) Backward Lexing

       Backward lexing has the task to find out whether a pre-context is fulfilled.
       But it does not stop, since multiple pre-contexts may still be fulfilled.
       Thus, the set of fulfilled pre-contexts is stored in 

                    ".pre_context_fulfilled_set"

       This list can be determined beforehand from the origin list. 

       NOTE: This type supports being a dictionary key by '__hash__' and '__eq__'.
             Required for the optional 'template compression'.
    """
    __slots__ = ("__pre_context_fulfilled_set")
    def __init__(self, OriginList):
        self.__pre_context_fulfilled_set = set([])
        for origin in ifilter(lambda origin: origin.is_acceptance(), OriginList):
            self.__pre_context_fulfilled_set.add(origin.pattern_id())

    def __hash__(self):
        return hash(len(self.__pre_context_fulfilled_set))

    def __eq__(self, Other):
        # NOTE: set([0, 1, 2]) == set([2, 1, 0]) 
        #       ... equal if elements are the same, order not important
        return self.pre_context_fulfilled_set == Other.pre_context_fulfilled_set

    def uniform_doors_f(self):
        return True

    def is_equal(self, Other):
        return self.__eq__(Other)

    @property
    def pre_context_fulfilled_set(self):
        return self.__pre_context_fulfilled_set

    def __repr__(self):
        if len(self.pre_context_fulfilled_set) == 0: return ""
        txt = ["    EntryBackward:\n"]
        txt.append("    pre-context-fulfilled = %s;\n" % repr(list(self.pre_context_fulfilled_set))[1:-1])
        return "".join(txt)

def repr_acceptance_id(Value, PatternStrF=True):
    if   Value == E_AcceptanceIDs.VOID:                       return "last_acceptance"
    elif Value == E_AcceptanceIDs.FAILURE:                    return "Failure"
    elif Value == E_AcceptanceIDs.TERMINAL_PRE_CONTEXT_CHECK: return "PreContextCheckTerminated"
    elif Value >= 0:                                    
        if PatternStrF: return "Pattern%i" % Value
        else:           return "%i" % Value
    else:                                               assert False

def repr_position_register(Register):
    if Register == E_PostContextIDs.NONE: return "position[Acceptance]"
    else:                                 return "position[PostContext_%i] " % Register

def repr_pre_context_id(Value):
    if   Value == E_PreContextIDs.NONE:          return "Always"
    elif Value == E_PreContextIDs.BEGIN_OF_LINE: return "BeginOfLine"
    elif Value >= 0:                             return "PreContext_%i" % Value
    else:                                        assert False

def repr_positioning(Positioning, PostContextID):
    if   Positioning == E_TransitionN.VOID: 
        return "pos = %s;" % repr_position_register(PostContextID)
    elif Positioning == E_TransitionN.LEXEME_START_PLUS_ONE: 
        return "pos = lexeme_start_p + 1; "
    elif Positioning > 0:   return "pos -= %i; " % Positioning
    elif Positioning == 0:  return ""
    else: 
        assert False

