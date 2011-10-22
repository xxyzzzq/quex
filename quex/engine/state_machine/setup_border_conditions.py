from   quex.engine.state_machine.core               import StateMachine, State
import quex.engine.state_machine.index              as     state_machine_index
import quex.engine.state_machine.setup_post_context as setup_post_context
import quex.engine.state_machine.nfa_to_dfa         as nfa_to_dfa
from   quex.engine.state_machine.state_core_info    import E_PreContextIDs

def do(sm, BeginOfLineF, EndOfLineF, DOS_CarriageReturnNewlineF=False):
    """DOS_CarriageReturnNewlineF == True:  
               '$' is implemented as post-condition '\r\n'. This is required
               or lexical analysers on DOS and Windows machines.
       DOS_CarriageReturnNewlineF == False:
               '$' is implemented as post-condition '\n' -- like the normal
               newline on Unix machines.
    """

    # (1) end of line 
    if EndOfLineF:
        # NOTE: This must come before 'Begin of File', because there's a post condition
        #       added, that enters new acceptance states.
        __end_of_line_condition(sm, DOS_CarriageReturnNewlineF)

    # (2) begin of line
    if BeginOfLineF: 
        # NOTE: EndOfLineF must be handled before. Reason ... see there.
        __begin_of_line_condition(sm, DOS_CarriageReturnNewlineF)
    return sm

def __end_of_line_condition(sm, DOS_CarriageReturnNewlineF):
    if not sm.core().post_context_f():
        # -- create a state machine that represents the post-condition
        # -- mount it to the core pattern as a post-condition
        post_sm = StateMachine()
        if not DOS_CarriageReturnNewlineF:
            post_sm.add_transition(post_sm.init_state_index, ord('\n'), AcceptanceF=True)
        else:
            aux_idx   = post_sm.add_transition(post_sm.init_state_index, ord('\r'), AcceptanceF=False)
            post_sm.add_transition(aux_idx, ord('\n'), AcceptanceF=True)
        
        # post conditions add an epsilon transition that has to be solved 
        # by translating state machine into a DFA
        sm = setup_post_context.do(sm, post_sm) 
        sm = nfa_to_dfa.do(sm)
        assert sm.has_origins() == False
        
    else:
        # mount 'newline or EndOfFile_Code' to the tail of pattern
        __add_line_border_at_end(sm, DOS_CarriageReturnNewlineF, InverseF=False)

def __begin_of_line_condition(sm, DOS_CarriageReturnNewlineF):
    """Begin of line in two cases:

         (1) last char was '\n'
         (2) the first character is not detected as begin of line, if the 
             pre-condition is non-trivial.
         
        A line begins always after '\n' so no check for '\r\n' is necessary.
        => DOS_CarriageReturnNewlineF = False
    """
    if sm.core().pre_context_sm() is not None:
        __add_line_border_at_end(sm.core().pre_context_sm(), 
                                 DOS_CarriageReturnNewlineF=False, InverseF=True)
    else:
        # mark all acceptance states with the 'trivial pre-condition BOL' flag
        for state in sm.get_acceptance_state_list():
            state.core().set_pre_context_id(E_PreContextIDs.BEGIN_OF_LINE)
        sm.core().set_pre_context_begin_of_line_f()
            

def __add_line_border_at_end(the_sm, DOS_CarriageReturnNewlineF, InverseF):     
    """Adds the condition 'newline or border character' at the end of the given
       state machine. Acceptance is only reached when the newline or border
       occurs. 
       
       This function is used for begin of line or end of line pre-conditions,
       thus: IT DOES NOT SETUP A POST-CONDITITION in the sense that output is
       scanned but cursor is being reset after match!  The caller provides the
       post-condition modifications itself, if needed.

       We simply append to each acceptance state the trigger '\n' or
       BorderCharacter that leads to the new acceptance.  The old acceptance
       state is annulated.  
    """    
    old_acceptance_state_list = the_sm.get_acceptance_state_list() 
    new_state_idx             = state_machine_index.get()
    new_state                 = State(StateIndex=new_state_idx)
    # New state must be just like any of the acceptance states (take the first).
    # The transition map, of course must be empty.
    new_state.set_cloned_core(old_acceptance_state_list[0].core())

    the_sm.states[new_state_idx] = new_state

    for state in old_acceptance_state_list:
        # (1) Transition '\n' --> Acceptance
        state.add_transition(ord('\n'), new_state_idx)
        
        if DOS_CarriageReturnNewlineF:
            # (3) Transition '\r\n' --> Acceptance
            aux_idx = the_sm.create_new_state(AcceptanceF=False)
            if not InverseF:
                state.add_transition(ord('\r'), aux_idx)
                the_sm.states[aux_idx].add_transition(ord('\n'), new_state_idx)
            else:
                state.add_transition(ord('\n'), aux_idx)
                the_sm.states[aux_idx].add_transition(ord('\r'), new_state_idx)

        # (-) Cancel acceptance of old state
        state.set_acceptance(False)
        state.core().set_input_position_store_f(False)
        state.core().set_input_position_restore_f(False)
        state.core().set_pre_context_id(E_PreContextIDs.NONE)
        #
    return new_state_idx    
