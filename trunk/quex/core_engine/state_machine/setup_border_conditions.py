from quex.core_engine.state_machine.core import StateMachine
import quex.core_engine.state_machine.setup_post_condition as setup_post_condition
import quex.core_engine.state_machine.nfa_to_dfa as nfa_to_dfa

def do(sm, BeginOfLineF, EndOfLineF, BeginOfFile_Code, EndOfFile_Code, 
       DOS_CarriageReturnNewlineF=False):
    """DOS_CarriageReturnNewlineF == True:  
               '$' is implemented as post-condition '\r\n'. This is required
               or lexical analysers on DOS and Windows machines.
       DOS_CarriageReturnNewlineF == False:
               '$' is implemented as post-condition '\n' -- like the normal
               newline on Unix machines.
    """

    def add_line_border_at_end(the_sm, BorderCode, DOS_CarriageReturnNewlineF):     
        """Adds the condition 'newline or border character' at the end 
           of the given state machine. Acceptance is only reached when 
           the newline or border occurs. 
           
           This function is used for begin of line or end of line pre-conditions, 
           thus: IT DOES NOT SETUP A POST-CONDITITION in the sense
           that output is scanned but cursor is being reset after match!
           The caller provides the post-condition modifications itself, if needed.

           We simply append to each acceptance state the trigger
           '\n' or BorderCharacter that leads to the new acceptance.
           The old acceptance state is annulated.
        """    
        state_idx_list = the_sm.get_acceptance_state_index_list() 
        new_state_idx = the_sm.create_new_state(AcceptanceF=True)
        for state_idx in state_idx_list:
            state = the_sm.states[state_idx]
            if not DOS_CarriageReturnNewlineF:
                the_sm.add_transition(state_idx, ord('\n'), new_state_idx)
            else:
                aux_idx = the_sm.add_transition(state_idx, ord('\r'), AcceptanceF=False)
                the_sm.add_transition(aux_idx, ord('\n'), new_state_idx)

            the_sm.add_transition(state_idx, BeginOfFile_Code, new_state_idx)
            #
            state.set_acceptance(False)
            state.set_store_input_position_f(False)
            state.set_post_conditioned_acceptance_f(False)
            state.set_trivial_pre_condition_begin_of_line(False)
            #
        return new_state_idx    

    # (*) begin of line
    if BeginOfLineF: 
        if sm.has_non_trivial_pre_condition():
            # begin of line in two cases:
            #  (1) last char was '\n'
            #  (2) at initialization, we supposed anyway that in this case the buffer needs to
            #      start with 'BeginOfFile_Code' just before the first letter.
            #
            #   => mount 'newline or 'BeginOfFile_Code' to the tail of the pre-condition
            #
            #  A line begins always after '\n' so no check for '\r\n' is necessary.
            #  => DOS_CarriageReturnNewlineF = False
            add_line_border_at_end(sm.pre_condition_state_machine, BeginOfFile_Code, 
                                   DOS_CarriageReturnNewlineF=False)
        else:
            # mark all acceptance states with the 'trivial pre-condition BOL' flag
            for state_idx, state in sm.states.items():
                if not state.is_acceptance(): continue
                if not state.has_origin():
                    state.add_origin(sm.get_id(), state_idx, True) 
                state.set_trivial_pre_condition_begin_of_line()
            
             
                
    # (*) end of line
    if EndOfLineF:
        if not sm.is_post_conditioned():
            # -- create a state machine that represents the post-condition
            # -- mount it to the core pattern as a post-condition
            post_sm = StateMachine()
            if not DOS_CarriageReturnNewlineF:
                state_idx = post_sm.add_transition(post_sm.init_state_index, ord('\n'), AcceptanceF=True)
            else:
                aux_idx   = post_sm.add_transition(post_sm.init_state_index, ord('\r'), AcceptanceF=False)
                state_idx = post_sm.add_transition(aux_idx, ord('\n'), AcceptanceF=True)
            post_sm.add_transition(post_sm.init_state_index, EndOfFile_Code, state_idx, AcceptanceF=True)
            
            # post conditions add an epsilon transition that has to be solved 
            # by translating state machine into a DFA
            sm = setup_post_condition.do(sm, post_sm) 
            sm = nfa_to_dfa.do(sm)
            sm.delete_meaningless_origins()
        
        else:
            # end of line in two cases:
            #  (1) next char is '\n' (or \r\n in case of DOS_CarriageReturnNewlineF==True)
            #  (2) at end of file, we supposed anyway that in this case the buffer needs to
            #      end with 'EndOfFile_Code' just before the first letter.
            #
            #  => mount 'newline or 'EndOfFile_Code' to the tail of pattern
            #
            new_state_idx = add_line_border_at_end(sm, EndOfFile_Code, 
                                                   DOS_CarriageReturnNewlineF)
            # -- the post-condition flag needs to be raised
            sm.states[new_state_idx].add_origin(sm.get_id(), new_state_idx, StoreInputPositionF=False)
            sm.states[new_state_idx].set_post_conditioned_acceptance_f(True)
            #
            if BeginOfLineF and sm.has_non_trivial_pre_condition() == False:
                sm.states[new_state_idx].set_trivial_pre_condition_begin_of_line()
            
    return sm
