
def do(IncidenceIdMap, ReloadF, DoorIdExit):
    """Brief: Generates a state machine that implements the transition
    to terminals upon the input falling into a number set. 
        
                 .------------.
                 | on_reentry |   
                 '------+-----'
                        |
               .-----------------.
               | character set 0 +---- - -> Incidence0
               |                 |
               | character set 1 +---- - -> Incidence1
               |                 |
               | character set 2 +---- - -> Incidence2
               |                 |
               |           (BLC) O
               |                 |         .---------.
               |            else +-------->| on_else |--- - -> DoorIdExit
               '-----------------'         '---------'

    The terminals related to the mentioned incidence ids are not implemented.
    If Setup.buffer_codec_transformation_info is defined the state machine
    is transformed accordingly.

    'on_reentry' handler is provided, in case that terminals what to re-
    enter the terminal map (loops). 
    
    'on_else' implements actions to be performed if some input occurs that 
    does not fall into one of the mentioned character sets. 

    Upon entry into a terminal related to the incidence ids, the input pointer
    stands right after the character which triggered the transition! The same
    is true for the 'on_else' terminal. Note, however, that 'on_else' appears
    when a not-covered character appears. 
    
    ARGUMENTS:

    IncidenceIdMap: List of tuples (NumberSet, IncidenceId) 

    ReloadF: If True, then a whole is left for the transition on buffer 
             limit code to the reload state.
        
    """
    sm       = StateMachine()
    iid_else = None
    blc_set  = NumberSet(Setup.buffer_limit_code)

    def add(sm, state, TriggerSet, IncidenceId):
        target_state_index = index.get()
        target_state       = sm.states[target_state_index]
        state.add_transition(TriggerSet, target_state_index)
        target_state.mark_self_as_origin(IncidenceId, 
                                         target_state_index)
        target_state.set_acceptance(True)

    def prepare_else(sm, state):
        covered_set = state.target_map.get_trigger_set_union()
        if ReloadF:               covered_set.unite_with(blc_set)
        if covered_set.is_all():  return
        if iid_else is None:      iid_else = dial_db.new_incidence_id()
        uncovered_set = covered_set.inverse()
        add(sm, state, uncovered_set, iid_else)

    sm         = StateMachine()
    init_state = sm.get_init_state()
    for character_set, incidence_id in CodeMap:
        # 'cliid' = unique command list incidence id.
        add(sm, init_state, character_set, incidence_id)

    dummy, sm = transformation.do_state_machine(sm)

    for state in sm.states.itervalues():
        prepare_else(state)

    # When the state machine is left upon occurrence of an else 
    # character. Then 
    if iid_else is None:
        terminal_else = None
    else:
        if Setup.variable_character_sizes_f():
            on_reentry = [ LexemeStartToReferenceP(Lng.INPUT_P()) ]
            on_else    = [ InputPToLexemeStartP() ]
        else:
            on_reentry = []
            on_else    = [ InputPDecrement() ]
        on_else.append(GotoDoorId(DoorIdExit))

        terminal_else = Terminal(on_else, "<ELSE>")
        terminal_else.set_incidence_id(iid_else)

    return sm, on_reentry, terminal_else

def get_count_command_list(CCInfo):
    cl = copy(CCInfo.command_list)

    cl.append(
        GotoDoorIdIfInputPNotEqualPointer(door_id_reentry, "LexemeEnd")
    )
    if cc_type == E_CharacterCountType.CHARACTER:
        cl.append(
            ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                          self.column_count_per_chunk)
        )
    cl.append(GotoDoorId(door_id_exit))

    return cl

def get_terminal(CLIID, CCInfo):
    code = get_count_command_list(CCInfo)
    name = CCInfo.trigger_set.get_string("hex")
    terminal = Terminal(code, name)
    terminal.set_incidence_id(CLIID)
    return terminal

def get_plain_terminal(IncidenceId, Code, Name):
    terminal = Terminal(Code, Name)
    terminal.set_incidence_id(IncidenceId)
    return terminal

def loopy():
    incidence_id_map = [
        (cc_info.trigger_set, cliid)
        for cliid, cc_info in count_command_map.iteritems()
    ]

    sm, on_reentry, on_inconsiderare, iid_inconsiderate = doodle(incidence_id_map, ReloadF)
    
    terminal_list = [
        get_terminal(cliid, cc_info)
        for cliid, cc_info in count_command_map.iteritems()
    ]
    terminal_list.append(
        get_plain_terminal(iid_inconsiderate, on_inconsiderate, "<inconsiderate>")
    )

    return sm, on_reentry, terminal_list

def _on_before_after_reload_prepare(LexemeF):
    """Actions to be performed before and after reload.

    RETURNS: 
    
        [0], [1]    Commands to be executed before and after buffer reload. 
                    This basically adapts the reference pointer for column 
                    number counting. 
                 
        None, None  If column number counting cannot profit from the a fixed
                    ColumnCountPerChunk (applying "column += (p-reference_p)*c")

    The LexemeF tells whether the current lexeme is important, i.e. treated
    by some handler. If not, the how buffer may be reloaded by setting the 
    lexeme start pointer to the input pointer.
    """
    on_before_reload = []
    on_after_reload  = []
    if self.column_count_per_chunk is not None:
        on_before_reload.append(
            ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                          self.column_count_per_chunk)
        )
        on_after_reload.append(
            ColumnCountReferencePSet(self.iterator_name)
        )

    if not LexemeF and not Setup.variable_character_sizes_f():
        # The lexeme start pointer defines the lower border of memory to be 
        # kept when reloading. Setting it to the input pointer allows for 
        # the whole buffer to be reloaded. THIS CAN ONLY BE DONE IF THE 
        # LEXEME IS NOT IMPORTANT!
        on_before_reload.append(
            LexemeStartToReferenceP(self.iterator_name)
        )

    return CommandList.from_iterable(on_before_reload), \
           CommandList.from_iterable(on_after_reload)


def get_analyzer():
    sm, on_reentry, terminal_list = loopy()

    analyzer = Analyzer(sm, EngineType, GlobalReloadState=GlobalReloadState)

      


def DELETE_get_state_machine(TerminalMap):
    # -- Generate for each character set that has the same counting action a
    #    transition in the state machine. 
    # -- Associate the target state with an 'AcceptanceID'.
    #    (AcceptanceID-s survive the transformation and NFA-to-DFA)
    # -- Store the relation between the counting action (given by the 'cliid')
    #    and the acceptance id.
    pass
