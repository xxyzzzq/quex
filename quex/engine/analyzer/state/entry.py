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
              (TransitionID(StateIndex, i), TransitionAction()) \
              for i in FromStateIndexList                                    \
        )
        dict.__init__(self, iterable)
        self.__state_index             = StateIndex
        self.__largest_used_door_sub_index = 0  # '0' is used for 'Door 0', i.e. reload entry

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

    def categorize(self, StateIndex):
        """Identifies command lists which are the same. Each unique command list
        receives a 'door_id' which identifies the entry into the state from where
        the command list is executed.
        """
        command_list_db = {}    # Helps to detect actions with same command list
        replacement_db  = None  # Tracks re-assignment of door-ids
        i               = 0
        def sort_key(X):
            return (X[0].state_index, X[0].from_state_index)

        for transition_id, action in sorted(self.items(), key=sort_key): # NOT: 'iteritems()'
            # If there was an action with the same command list, then assign
            # the same door id. Leave the action intact! May be, it is modified
            # later and will differ from the currently same action.
            new_door_id = command_list_db.get(action.command_list)
            if new_door_id is None:
                i += 1
                new_door_id = DoorID(StateIndex, i)
                command_list_db[action.command_list] = new_door_id

            if action.door_id is not None:                     # Keep track of changed
                replacement_db[action.door_id] = new_door_id   # DoorIds
            action.door_id = new_door_id

        self.__largest_used_door_sub_index = i  # '0' is used for 'Door 0', i.e. reload entry
        return replacement_db

    @property 
    def largest_used_door_sub_index(self):
        return self.__largest_used_door_sub_index

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
        
        action = self.get(tmp_transition_id)
        if action is None: return None
        return action.door_id

    def get_door_id_by_command_list(self, TheCommandList):
        """Finds the DoorID of the door that implements TheCommandList.
           RETURNS: None if no such door exists that implements TheCommandList.
        """
        if TheCommandList.is_empty():
            return DoorID(self.__state_index, 0) # 'Door 0' is sure to not do anything!

        for action in self.itervalues():
            if action.command_list == TheCommandList:
                return action.door_id
        return None

    def has_commands_other_than_MegaState_Command(self):
        for action in self.itervalues():
            for found in (x for x in action.command_list if not isinstance(x, MegaState_Command)):
                return True

        return False

class Entry(object):
    """________________________________________________________________________

    An Entry object stores commands to be executed at entry into a state
    depending on a particular source state; and may be also depending on
    the particular trigger.
    
    BASICS _________________________________________________________________

    To keep track of entry actions, CommandList-s need to 
    be associated with a TransitionID-s, i.e. pairs of (state_index,
    from_state_index). This happens in the member '.action_db', i.e.
    
       .action_db:    TransitionID --> TransitionAction

    where a TransitionID consists of: .from_state_index
                                      .state_index
                                      .trigger_id 
 
    and a TransitionAction consists of: .door_id
                                        .command_list
                                        
    where '.door_id'  identifies a specific door  of the  entry into  the state.
    It is distinctly associated with a list of commands '.command_list'. The 
    commands of '.command_list' are executed if the state is entered by
    a transition given with the key's TransitionID. A call to 

                            action_db.categorize()

    ensures that
                                  1      1
                        DoorID  <---------> CommandList
   
    In words: 
    
       -- each TransitionAction *has a* valid door_id. That is, every list of
          commands is identified with a door_id.

       -- The door_id *distinctly* determines the command list (in the entry). 
          That is, door_id-s of TransitionAction-s differ if and only if their
          command lists are different.
                  
    Later on in the code generation, a 'door tree' is generated to produce
    optimized code which profits from common commands in command lists. But,
    for now, it is important to remember:

              .---------------------------------------------------.
              |  A DoorID distinctly identifies a CommandList to  |
              |       be executed the at entry of a state.        |
              '---------------------------------------------------'
    """

    __slots__ = ("__state_index", "__action_db")

    def __init__(self, StateIndex, FromStateIndexList):
        # map:  (from_state_index) --> list of actions to be taken if state is entered 
        #                              'from_state_index' for a given pre-context.
        # if len(FromStateIndexList) == 0: FromStateIndexList = [ E_StateIndices.NONE ]
        self.__state_index = StateIndex
        self.__action_db   = EntryActionDB(StateIndex, FromStateIndexList)

    @property
    def state_index(self): 
        return self.__state_index

    @property
    def action_db(self):
        return self.__action_db

    @property
    def door_tree_root(self): 
        """The door_tree_root is determined by 'build_door_tree()'"""
        assert self.__door_tree_root is not None
        return self.__door_tree_root

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

