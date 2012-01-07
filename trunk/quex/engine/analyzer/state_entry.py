import quex.engine.analyzer.state_entry_action as entry_action
from   quex.blackboard          import setup as Setup, \
                                       E_StateIndices,  E_PreContextIDs,  \
                                       E_AcceptanceIDs, E_PostContextIDs, \
                                       E_TransitionN
from   collections              import defaultdict, namedtuple
from   operator                 import attrgetter
from   itertools                import ifilter, combinations, islice

class Entry(object):
    """An entry has potentially the following tasks:
    
          (1) Storing information about positioning represented by objects 
              of type 'entry_action.StoreInputPosition'.

          (2) Storing information about an acceptance. represented by objects
              of type 'entry_action.StoreInputPosition'.
              
       Entry actions are relative from which state it is entered. Thus, an 
       object of this class contains a dictionary that maps:

                 from_state_index  --> list of entry actions

    """
    __slots__ = ("__uniform_doors_f", "__doors_db", "__source_state_to_group_db", "__door_tree_root")

    def __init__(self, FromStateIndexList, PreContextFulfilledID_List=None):
        # map:  (from_state_index) --> list of actions to be taken if state is entered 
        #                              'from_state_index' for a given pre-context.
        if len(FromStateIndexList) == 0:
            FromStateIndexList = [ E_StateIndices.NONE ]
        self.__doors_db = dict((i, entry_action.ActionDB_Entry(i)) for i in FromStateIndexList)

        # Are the actions for all doors the same?
        self.__uniform_doors_f = None 

        # Function 'categorize_action_lists()' fills the following members
        self.__source_state_to_group_db = None # map: source state index to group_id in door tree
        self.__door_tree_root           = None # The root of the door tree.

        # Only for 'Backward Detecting Pre-Contexts'.
        if PreContextFulfilledID_List is not None:
            pre_context_ok_action_list = [ entry_action.PreConditionOK(pre_context_id) \
                                           for pre_context_id in PreContextFulfilledID_List ]
            for entry in self.__doors_db.itervalues():
                entry.action_list.misc.update(pre_context_ok_action_list)

    def doors_accept(self, FromStateIndex, PathTraceList):
        """At entry via 'FromStateIndex' implement an acceptance pattern that 
           is determined via 'PathTraceList'. This function is called upon the
           detection of a state that restores acceptance. The previous state 
           must be of uniform acceptance (does not restore). At the entry of 
           this function we implement the acceptance pattern of the previous
           state.
        """
        # Construct the Accepter from PathTraceList
        accepter = entry_action.Accepter()
        for path_trace in PathTraceList:
            accepter.add(path_trace.pre_context_id, path_trace.pattern_id)

        self.__doors_db[FromStateIndex].action_list.accepter = accepter

    def doors_accepter_add_front(self, PreContextID, PatternID):
        """Add an acceptance at the top of each accepter at every door. If there
           is no accepter in a door it is created.
        """
        for door in self.__doors_db.itervalues():
            # Catch the accepter, if there is already one, of not create one.
            if door.action_list.accepter is None: 
                door.action_list.accepter = entry_action.Accepter()
            door.action_list.accepter.insert_front(PreContextID, PatternID)

    def doors_store(self, FromStateIndex, PreContextID, PositionRegister, Offset):
        # Add 'store input position' to specific door. See 'entry_action.StoreInputPosition'
        # comment for the reason why we do not store pre-context-id.
        entry = entry_action.StoreInputPosition(PreContextID, PositionRegister, Offset)
        self.__doors_db[FromStateIndex].action_list.misc.add(entry)

    def door_number(self):
        total_size = len(self.__doors_db)
        # Note, that total_size can be '0' in the 'independent_of_source_state' case
        if self.__uniform_doors_f: return min(1, total_size)
        else:                      return total_size

    @property
    def source_state_to_group_db(self):
        """The source_state_to_group_db is determined by 'categorize_action_lists()'"""
        return self.__source_state_to_group_db

    @property
    def door_tree_root(self): 
        """The door_tree_root is determined by 'categorize_action_lists()'"""
        return self.__door_tree_root

    def has_accepter(self):
        for door in self.__doors_db.itervalues():
            for action in door.action_list:
                if isinstance(action, entry_action.Accepter): return True
        return False

    @property
    def doors_db(self):
        return self.__doors_db

    def __hash__(self):
        result = 0
        for door in self.__doors_db.itervalues():
            result += len(door.action_list)
        return result

    def __eq__(self, Other):
        if len(self.__doors_db) != len(Other.__doors_db): 
            return False
        for from_state_index, door in self.__doors_db.iteritems():
            other_door = Other.__doors_db.get(from_state_index)
            if other_door is None: return False
            if door.action_list != door.other_action_list: return False
        return True

    def is_equal(self, Other):
        # Maybe, we can delete this ...
        return self.__eq__(self, Other)

    def uniform_doors_f(self): 
        return self.__uniform_doors_f

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

           -- The PositionRegisterMap shows how condition register indices must be 
              replaced. This is a result from analysis about what registers can
              actually be shared.

           -- If a position for a post-context is stored in the unconditional
              case, then all pre-contexted position storages of the same post-
              context are superfluous.

           -- If the entry into the state behaves the same for all 'from'
              states then the entry is independent_of_source_state.
        
           -- Call to 'categorize_action_lists()' where action lists are grouped
              and hierarchically ordered.

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
            if door.action_list.is_empty(): continue
            change_f = False
            for action in door.action_list.misc:
                if isinstance(action, entry_action.StoreInputPosition):
                    # Replace position register according to 'PositionRegisterMap'
                    action.position_register = PositionRegisterMap[action.position_register]
                    change_f = True
            # If there was a replacement, ensure that each action appears only once
            if change_f:
                # Adding one by one ensures that double entries are avoided
                door.action_list.misc = set(x for x in door.action_list.misc)

        # (*) If a door stores the input position in register unconditionally,
        #     then all other conditions concerning the storage in that register
        #     are nonessential.
        for door in self.__doors_db.itervalues():
            for action in list(x for x in door.action_list \
                               if     isinstance(x, entry_action.StoreInputPosition) \
                                  and x.pre_context_id == E_PreContextIDs.NONE):
                for x in list(x for x in door.action_list.misc \
                              if isinstance(x, entry_action.StoreInputPosition)):
                    if x.position_register == action.position_register and x.pre_context_id != E_PreContextIDs.NONE:
                        door.action_list.misc.remove(x)

        # (*) Categorize action lists
        self.__source_state_to_group_db, \
        self.__door_tree_root            = entry_action.categorize_action_lists(self.__doors_db)

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
            for action in sorted(StorerList, key=attrgetter("pre_context_id", "position_register")):
                if action.pre_context_id != E_PreContextIDs.NONE:
                    txt.append("if '%s': " % repr_pre_context_id(action.pre_context_id))
                if action.offset == 0:
                    txt.append("%s = input_p;\n" % repr_position_register(action.position_register))
                else:
                    txt.append("%s = input_p - %i;\n" % (repr_position_register(action.position_register), 
                                                          action.offset))
            return txt

        def get_pre_context_oks(PCOKList):
            txt = []
            for action in sorted(PCOKList, key=attrgetter("pre_context_id")):
                txt.append("%s" % repr(action))
            return txt

        result = []
        for from_state_index, door in self.__doors_db.iteritems():
            accept_action_list = []
            store_action_list  = []
            pcok_action_list   = []
            for action in door.action_list:
                if isinstance(action, entry_action.Accepter): 
                    accept_action_list.append(action)
                elif isinstance(action, entry_action.PreConditionOK):
                    pcok_action_list.append(action)
                else:
                    store_action_list.append(action)

            result.append("    .from %s:" % repr(from_state_index).replace("L", ""))
            a_txt = get_accepters(accept_action_list)
            s_txt = get_storers(store_action_list)
            p_txt = get_pre_context_oks(pcok_action_list)
            content = "".join(a_txt + s_txt + p_txt)
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

