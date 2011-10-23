# (C) 2005-2010 Frank-Rene Schaefer
# ABSOLUTELY NO WARRANTY
###############################################################################
from   quex.engine.state_machine.core import StateMachine, State
import quex.engine.state_machine.index as index

def do(StateMachineList, CommonTerminalStateF=True, CloneF=True):
    """Connect state machines paralell.

       CommonTerminalStateF tells wether the state machines shall trigger 
                            to a common terminal. This is necessary if the
                            state machines are part of a bigger construction.

                            When the ready-to-rumble pattern state machines
                            are to be combined into a single analyzer, the
                            flag must be set to 'False'.

       CloneF               Controls if state machine list is cloned or not.
                            If the single state machines are no longer required after
                            construction, the CloneF can be set to False.

                            If Cloning is disabled the state machines themselves
                            will be altered--which brings some advantage in speed.
    """
    assert type(StateMachineList) == list
    assert len(StateMachineList) != 0
    assert map(lambda x: x.__class__.__name__, StateMachineList) == ["StateMachine"] * len(StateMachineList)
              
    # filter out empty state machines from the consideration          
    state_machine_list            = [ sm for sm in StateMachineList if not sm.is_empty() ]
    empty_state_machine_occured_f = len(state_machine_list) != len(StateMachineList)

    if len(state_machine_list) < 2:
        if len(state_machine_list) < 1: result = StateMachine()
        else:                           result = state_machine_list[0]

        if empty_state_machine_occured_f:
            result = __add_free_pass(result)
        return result

    # (*) need to clone the state machines, i.e. provide their internal
    #     states with new ids, but the 'behavior' remains. This allows
    #     state machines to appear twice, or being used in 'larger'
    #     conglomerates.
    if CloneF:
        clone_list = map(lambda sm: sm.clone(), state_machine_list)
    else:
        clone_list = state_machine_list

    # (*) collect all transitions from both state machines into a single one
    #     (clone to ensure unique identifiers of states)
    new_init_state = State.new_merged_core_state((clone.get_init_state() for clone in clone_list), 
                                                 ClearF=True)
    result         = StateMachine(InitState=new_init_state)

    for clone in clone_list:
        result.states.update(clone.states)

    # (*) add additional **init** and **end** state
    #     NOTE: when the result state machine was created, it already contains a 
    #           new initial state index. thus at this point only the new terminal
    #           state has to be created. 
    #     NOTE: it is essential that the acceptance flag stays False, at this
    #           point in time, so that the mounting operations only happen on
    #           the old acceptance states. Later the acceptance state is raised
    #           to 'accepted' (see below)
    new_terminal_state_index = -1L
    if CommonTerminalStateF:
        new_terminal_state_index = index.get()
        result.states[new_terminal_state_index] = \
                    State.new_merged_core_state(result.get_acceptance_state_list(), \
                                                ClearF=True)
    
    # (*) Connect from the new initial state to the initial states of the
    #     clones via epsilon transition. 
    #     Connect from each success state of the clones to the new end state
    #     via epsilon transition.
    for clone in clone_list:
        result.mount_to_initial_state(clone.init_state_index)

    if CommonTerminalStateF:
        result.mount_to_acceptance_states(new_terminal_state_index,
                                          CancelStartAcceptanceStateF=False)

    # (*) If there was an empty state machine, a 'free pass' is added
    if empty_state_machine_occured_f:
        result = __add_free_pass(result, new_terminal_state_index)

    return result

def __add_free_pass(result_state_machine,
                    TerminationStateIdx=-1):
    """Add an optional 'free pass' if there was an empty state.  
       If there was an empty state, then the number of elements in the list changed
       in case there was an empty state one has to add a 'free pass' from begin to 
       the final acceptance state.   
    """
    if TerminationStateIdx == -1:
        acceptance_state_index_list = result_state_machine.get_acceptance_state_index_list()
        assert len(acceptance_state_index_list) != 0, \
               "resulting state machine has no acceptance state!"
        TerminationStateIdx = acceptance_state_index_list[0]

    result_state_machine.add_epsilon_transition(result_state_machine.init_state_index, 
                                                TerminationStateIdx)
    return result_state_machine

