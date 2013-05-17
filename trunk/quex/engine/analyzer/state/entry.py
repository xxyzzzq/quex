import quex.engine.analyzer.state.entry_action as entry_action
from   quex.engine.analyzer.state.entry_action import TransitionID, TransitionAction, DoorID
from   quex.blackboard import E_PreContextIDs,  \
                              E_AcceptanceIDs, E_PostContextIDs, \
                              E_TransitionN, E_StateIndices, E_TriggerIDs
from   operator        import attrgetter

tmp_transition_id = TransitionID(E_StateIndices.VOID, E_StateIndices.VOID)

class EntryActionDB(dict):
    def __init__(self, StateIndex, FromStateIndexList):
        """Assume that 'Iterable' provides all TransitionID-s which may ever
           appear in the action_db. If this is not the case, then a self[tid]
           may fail somewhere down the lines.
        """
        iterable = (                                                         \
              (TransitionID(StateIndex, i), TransitionAction(StateIndex, i)) \
              for i in FromStateIndexList                                    \
        )
        dict.__init__(self, iterable)
        self.__state_index = StateIndex

    def add_Accepter(self, PreContextID, PatternID):
        """Add an acceptance at the top of each accepter at every door. If there
           is no accepter in a door it is created.
        """
        for transition_action in self.itervalues():
            # Catch the accepter, if there is already one, of not create one.
            if transition_action.command_list.accepter is None: 
                transition_action.command_list.accepter = entry_action.Accepter()
            transition_action.command_list.accepter.add(PreContextID, PatternID)
            # NOT: transition_action.command_list.accepter.clean_up()
            #      The list might be deliberately ordered differently

    def add_specific_Accepter(self, FromStateIndex, PathTraceList):
        """At entry via 'FromStateIndex' implement an acceptance pattern that 
           is determined via 'PathTraceList'. This function is called upon the
           detection of a state that restores acceptance. The previous state 
           must be of uniform acceptance (does not restore). At the entry of 
           this function we implement the acceptance pattern of the previous
           state.
        """
        global tmp_transition_id
        # Construct the Accepter from PathTraceList
        accepter = entry_action.Accepter(PathTraceList)

        tmp_transition_id.state_index      = self.__state_index
        tmp_transition_id.from_state_index = FromStateIndex
        tmp_transition_id.trigger_id       = E_TriggerIDs.NONE
        self[tmp_transition_id].command_list.accepter = accepter

    def has_Accepter(self):
        for action in self.itervalues():
            for cmd in action.command_list:
                if isinstance(cmd, entry_action.Accepter): return True
        return False

    def add_StoreInputPosition(self, FromStateIndex, PreContextID, PositionRegister, Offset):
        """Add 'store input position' to specific door. See 'entry_action.StoreInputPosition'
           comment for the reason why we do not store pre-context-id.
        """
        global tmp_transition_id
        entry = entry_action.StoreInputPosition(PreContextID, PositionRegister, Offset)
        tmp_transition_id.state_index      = self.__state_index
        tmp_transition_id.from_state_index = FromStateIndex
        tmp_transition_id.trigger_id       = E_TriggerIDs.NONE
        self[tmp_transition_id].command_list.misc.add(entry)

    def get_action(self, StateIndex, FromStateIndex, TriggerId=E_TriggerIDs.NONE):
        global tmp_transition_id
        tmp_transition_id.state_index      = StateIndex
        tmp_transition_id.from_state_index = FromStateIndex
        tmp_transition_id.trigger_id       = TriggerId
        return self.get(tmp_transition_id)

    def delete(self, StateIndex, FromStateIndex, TriggerId=E_TriggerIDs.NONE):
        global tmp_transition_id
        tmp_transition_id.state_index      = StateIndex
        tmp_transition_id.from_state_index = FromStateIndex
        tmp_transition_id.trigger_id       = TriggerId
        del self[tmp_transition_id]

    def reconfigure_position_registers(self, PositionRegisterMap):
        """Originally, each pattern gets its own position register if it is
        required to store/restore the input position. The 'PositionRegisterMap'
        is a result of an analysis which tells whether some registers may
        actually be shared. This function does the replacement of positioning
        registers based on what is given in 'PositionRegisterMap'.
        """
        if PositionRegisterMap is None or len(PositionRegisterMap) == 0: 
            return

        def store_input_position(iterable):
            for cmd in iterable:
                if isinstance(cmd, entry_action.StoreInputPosition):
                    yield cmd

        for action in self.itervalues():
            if action.command_list.is_empty(): continue
            change_f = False
            for cmd in store_input_position(action.command_list.misc):
                # Replace position register according to 'PositionRegisterMap'
                cmd.position_register = PositionRegisterMap[cmd.position_register]
                change_f = True
            # If there was a replacement, ensure that each command appears only once
            if change_f:
                # Adding one by one ensures that double entries are avoided
                action.command_list.misc = set(x for x in action.command_list.misc)
        return

    def delete_nonsense_conditions(self):
        """If a command list stores the input position in register unconditionally,
        then all other conditions concerning the storage in that register are 
        nonsensical.
        """
        for action in self.itervalues():
            for cmd in list(x for x in action.command_list \
                            if     isinstance(x, entry_action.StoreInputPosition) \
                               and x.pre_context_id == E_PreContextIDs.NONE):
                for x in list(x for x in action.command_list.misc \
                              if isinstance(x, entry_action.StoreInputPosition)):
                    if x.position_register == cmd.position_register and x.pre_context_id != E_PreContextIDs.NONE:
                        try:    action.command_list.misc.remove(x)
                        except: pass
        return

    def has_transitions_to_door_id(self, DoorId):
        for action in self.itervalues():
            if action.door_id == DoorId:
                return True
        return False

    def get_transition_id_list(self, DoorId):
        return [ 
           transition_id for transition_id, action in self.iteritems()
                         if action.door_id == DoorId 
        ]

class Entry(object):
    """________________________________________________________________________

    An Entry object stores commands to be executed at entry into a state
    depending on a particular source state.
    
    BASICS _________________________________________________________________

    To keep track of entry actions, CommandList-s need to 
    be associated with a TransitionID-s, i.e. pairs of (state_index,
    from_state_index). This happens in the member '.action_db', i.e.
    
       .action_db:    TransitionID --> TransitionAction

    where a TransitionID consists of: .from_state_index
                                      .state_index
                                      .trigger_id 
 
    and a TransitionAction consists of: .transition_id
                                        .command_list
                                        
    where '.command_list' are commands that are executed for the given
    transition.

    The actions associated with transitions may be equal or have many
    commonalities.  In order to avoid multiple definitions of the same action,
    a 'door tree' is constructed.  Now, transitions need to be associated with
    doors into the entry. The corresponding door to an action is available
    at 'action.door_id' after 'door_tree_configure()' has been
    called.

    DOOR TREE ______________________________________________________________

    For code generation, the TransitionActions are organized more efficiently.
    Many transitions may share some commands, so that they could actually enter
    the state through the same or similar doors. Example:

        (4, from 1) --> accept 4711; store input position;
        (4, from 2) --> accept 4711; 
        (4, from 2) --> nothing;

    Then, the entry could look like this:

        Door2: store input position; 
               goto Door1;
        Door1: accept 4711; 
               goto Door0;
        Door0: /* nothing */

        ... the transition map ...

    This configuration is done in function 'door_tree_configure()'. As a result
    the command list in actions of 'self.action_db' contain a '.door_id' which
    tells about what door needs to be entered so that the list of commands is
    executed. 

    BRIEF REMARK: _________________________________________________________

    Before 'door_tree_configure()' is called no assumptions about doors
    can be made. Then, only information about what transition causes what
    action can be provided.
    ___________________________________________________________________________
    """
    __slots__ = ("__state_index", "__uniform_doors_f", "__action_db", "__transition_db", "__door_tree_root")

    def __init__(self, StateIndex, FromStateIndexList, PreContextFulfilledID_List=None):
        # map:  (from_state_index) --> list of actions to be taken if state is entered 
        #                              'from_state_index' for a given pre-context.
        # if len(FromStateIndexList) == 0: FromStateIndexList = [ E_StateIndices.NONE ]
        self.__state_index = StateIndex
        self.__action_db   = EntryActionDB(StateIndex, FromStateIndexList)

        # Are the actions for all doors the same?
        self.__uniform_doors_f = None 

        # Function 'categorize_command_lists()' fills the following members
        self.__transition_db  = None # map: door_id       --> transition_id
        self.__door_tree_root = None # The root of the door tree.

        # Only for 'Backward Detecting Pre-Contexts'.
        if PreContextFulfilledID_List is not None:
            pre_context_ok_command_list = [ entry_action.PreConditionOK(pre_context_id) \
                                            for pre_context_id in PreContextFulfilledID_List ]
            for transition_action in self.__action_db.itervalues():
                transition_action.command_list.misc.update(pre_context_ok_command_list)

    @property
    def state_index(self): 
        return self.__state_index

    @property
    def action_db(self):
        return self.__action_db

    @property
    def door_tree_root(self): 
        """The door_tree_root is determined by 'categorize_command_lists()'"""
        assert self.__door_tree_root is not None
        return self.__door_tree_root

    def get_door_id(self, StateIndex, FromStateIndex, TriggerId=E_TriggerIDs.NONE):
        """RETURN: DoorID of the door which implements the transition 
                          (FromStateIndex, StateIndex).
                   None,  if the transition is not implemented in this
                          state.
        """
        global tmp_transition_id
        tmp_transition_id.state_index      = StateIndex
        tmp_transition_id.from_state_index = FromStateIndex
        tmp_transition_id.trigger_id       = TriggerId
        
        action = self.__action_db.get(tmp_transition_id)
        if action is None: return None
        return action.door_id

    def get_door_id_by_command_list(self, TheCommandList):
        """Finds the DoorID of the door that implements TheCommandList.
           RETURNS: None if no such door exists that implements TheCommandList.
        """
        assert self.__door_tree_root is not None, "door_tree_configure() has not yet been called!"

        if TheCommandList.is_empty():
            return DoorID(self.__state_index, 0) # 'Door 0' is sure to not do anything!

        for action in self.action_db.itervalues():
            if action.command_list == TheCommandList:
                return action.door_id
        return None

    def door_id_update(self, DoorId):
        return None # Normal States do not need to update door ids; only AbsorbedState-s.

    def __hash__(self):
        xor_sum = 0
        for door in self.__action_db.itervalues():
            xor_sum ^= hash(door.command_list)
        return xor_sum

    def __eq__(self, Other):
        assert self.__door_tree_root is not None
        return self.__door_tree_root.is_equivalent(Other.__door_tree_root)

    def is_uniform(self, Other):
        assert self.__door_tree_root is not None
        return self.__door_tree_root.is_equivalent(Other.__door_tree_root)

    def is_equal(self, Other):
        # Maybe, we can delete this ...
        return self.__eq__(self, Other)

    def uniform_doors_f(self): 
        return self.__uniform_doors_f

    def _door_tree_configure_core(self):
        """Configure the 'door tree' (see module 'entry_action).

           BEFORE: An 'action_db' maps 

                   TransitionID  ---> CommandList

           That is, the action_db tells for a given transition (state_index,
           from_state_index) what commands are to be executed. Based on 
           action_db a 'door tree' is configured. The door tree profits from
           the fact, that some commands may be the same for more than one 
           transition into the state. Now, the state can be entered via these
           doors.
           
           AFTER: Each command list in 'ActionDB' has the 'door_id' set, i.e.

              self.action_db[door_id].door_id = something.

        """
        # (*) Categorize action lists

        # NOTE: The transition from 'NONE' does not enter the door tree.
        #       It appears only in the init state when the thread of 
        #       control drops into the first state. The from 'NONE' door
        #       is implemented referring to '.action_db.get_action(...)'.
        transition_action_list = [ 
            transition_action.clone() 
            for transition_id, transition_action in self.__action_db.iteritems() 
            if transition_id.from_state_index != E_StateIndices.NONE
        ]

        door_db,       \
        self.__door_tree_root = entry_action.categorize_command_lists(self.__state_index, transition_action_list)
        assert self.__door_tree_root is not None

        return door_db

    def door_tree_configure(self):
        """This function may be overloaded, so that derived classes (e.g. MegaState_Entry)
        can do other things with the information provided in 'door_db'.
        """
        door_db = self._door_tree_configure_core()
        for transition_id, door_id in door_db.iteritems():
            self.__action_db[transition_id].door_id = door_id

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

        def get_set_template_state_keys(SetTemplateStateKeyList):
            txt = []
            for action in sorted(SetTemplateStateKeyList, key=attrgetter("value")):
                txt.append("%s" % repr(action))
            return txt

        def get_set_path_iterator_keys(SetPathIteratorKeyList):
            txt = []
            for action in sorted(SetPathIteratorKeyList, key=attrgetter("path_walker_id", "path_id", "offset")):
                txt.append("%s" % repr(action))
            return txt

        result = []
        for transition_id, door in sorted(self.__action_db.iteritems(),key=lambda x: x[0].from_state_index):
            accept_command_list = []
            store_command_list  = []
            pcok_command_list   = []
            ssk_command_list    = []
            spi_command_list    = []
            for action in door.command_list:
                if isinstance(action, entry_action.Accepter): 
                    accept_command_list.append(action)
                elif isinstance(action, entry_action.PreConditionOK):
                    pcok_command_list.append(action)
                elif isinstance(action, entry_action.SetTemplateStateKey):
                    ssk_command_list.append(action)
                elif isinstance(action, entry_action.SetPathIterator):
                    spi_command_list.append(action)
                else:
                    store_command_list.append(action)

            result.append("    .from %s:" % repr(transition_id.from_state_index).replace("L", ""))
            a_txt  = get_accepters(accept_command_list)
            s_txt  = get_storers(store_command_list)
            p_txt  = get_pre_context_oks(pcok_command_list)
            sk_txt = get_set_template_state_keys(ssk_command_list)
            pi_txt = get_set_path_iterator_keys(spi_command_list)
            content = "".join(a_txt + s_txt + p_txt + sk_txt + pi_txt)
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

def repr_positioning(Positioning, PositionRegisterID):
    if   Positioning == E_TransitionN.VOID: 
        return "pos = %s;" % repr_position_register(PositionRegisterID)
    elif Positioning == E_TransitionN.LEXEME_START_PLUS_ONE: 
        return "pos = lexeme_start_p + 1; "
    elif Positioning > 0:   
        return "pos -= %i; " % Positioning
    elif Positioning == 0:  
        return ""
    else: 
        assert False

