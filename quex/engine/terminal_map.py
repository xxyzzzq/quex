from   quex.engine.state_machine.core             import StateMachine
import quex.engine.state_machine.index            as     index
import quex.engine.state_machine.transformation   as     transformation
from   quex.engine.interval_handling              import NumberSet
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.analyzer.commands              import InputPDecrement, \
                                                         InputPToLexemeStartP, \
                                                         GotoDoorId, \
                                                         LexemeStartToReferenceP
from   quex.engine.analyzer.terminal.core         import Terminal
from   quex.engine.generator.code.core            import CodeTerminal

from  quex.blackboard import setup as Setup, \
                             Lng

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
    blc_set  = NumberSet(Setup.buffer_limit_code)

    def add(sm, StateIndex, TriggerSet, IncidenceId):
        target_state_index = sm.add_transition(StateIndex, TriggerSet)
        target_state       = sm.states[target_state_index]
        target_state.mark_self_as_origin(IncidenceId, target_state_index)
        target_state.set_acceptance(True)

    def prepare_else(sm, StateIndex, iid_else):
        state       = sm.states[StateIndex]
        covered_set = state.target_map.get_trigger_set_union()
        if ReloadF:               covered_set.unite_with(blc_set)
        if covered_set.is_all():  return iid_else
        if iid_else is None:      iid_else = dial_db.new_incidence_id()
        uncovered_set = covered_set.inverse()
        add(sm, StateIndex, uncovered_set, iid_else)
        return iid_else

    sm         = StateMachine()
    init_state = sm.get_init_state()
    for character_set, incidence_id in IncidenceIdMap:
        # 'cliid' = unique command list incidence id.
        add(sm, sm.init_state_index, character_set, incidence_id)

    print "#smc:", sm
    dummy, sm = transformation.do_state_machine(sm)

    iid_else = None
    for state_index in sm.states.keys():
        iid_else = prepare_else(sm, state_index, iid_else)

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

        terminal_else = Terminal(CodeTerminal([Lng.COMMAND(cmd) for cmd in on_else]), "<ELSE>")
        terminal_else.set_incidence_id(iid_else)

    print "#smc1", sm
    return sm, on_reentry, terminal_else

def get_before_and_after_reload():
    """The 'lexeme_start_p' restricts the amount of data which is load into the
    buffer upon reload--if the lexeme needs to be maintained. If the lexeme
    does not need to be maintained, then the whole buffer can be refilled.
    
    For this, the 'lexeme_start_p' is set to the input pointer. 
    
    EXCEPTION: Variable character sizes. There, the 'lexeme_start_p' is used
    to mark the begin of the current letter. However, letters are short, so 
    the drawback is tiny.

    RETURN: [0] on_before_reload
            [1] on_after_reload
    """
    if not Setup.variable_character_sizes_f():
        return [], []

    return [ LexemeStartToReferenceP(Lng.INPUT_P())], \
           [ InputPToLexemeStartP() ]

