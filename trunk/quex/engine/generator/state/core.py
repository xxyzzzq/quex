from   quex.engine.analyzer.core                    import Analyzer
from   quex.engine.analyzer.state.core              import AnalyzerState
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.entry            as entry
import quex.engine.generator.state.drop_out         as drop_out
from   quex.engine.generator.languages.address      import get_label, get_address
from   quex.blackboard                              import setup as Setup, E_InputActions

LanguageDB = None

def do(code, TheState, TheAnalyzer):
    global LanguageDB
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    LanguageDB = Setup.language_db
    txt        = []

    # (*) Entry _______________________________________________________________
    entry_do(txt, TheState, TheAnalyzer)

    # (*) Access the triggering character _____________________________________
    input_do(txt, TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    tm = transition_block.prepare_transition_map(TheState.transition_map, 
                                                 TheState.index, 
                                                 TheState.init_state_f, 
                                                 TheAnalyzer = TheAnalyzer)

    transition_block.do(txt, tm)

    # (*) Drop Out ____________________________________________________________
    drop_out.do(txt, TheState.index, TheState.drop_out, TheAnalyzer)

    # ( ) Side entry to init state (if necessary)
    side_entry_do(txt, TheState, TheAnalyzer)

    # (*) Cleaning Up _________________________________________________________
    for i, x in enumerate(txt):
        assert not isinstance(x, list), repr(txt[i-2:i+2])
        assert not x is None, txt[i-2:i+2]

    code.extend(txt)

def entry_do(txt, TheState, TheAnalyzer):
    if not TheState.init_state_forward_f:
        # The very normal entry into a normal state
        entry.do(txt, TheState, TheAnalyzer)
        return

    # Init state in forward direction: there is no increment of input_p
    # when first entered. If the state machine requires a side entry to the
    # init state, it is implemented in 'side_entry_do()' and it jumps to
    # the LABEL INIT STATE TRANSITION BLOCK from there.
    if TheAnalyzer.has_transition_to_init_state():
        txt.append("%s: /* INIT_STATE_TRANSITION_BLOCK */\n" \
                   % get_label("$init_state_transition_block", TheState.index))

    # The Init State: Implement the 'NONE' door. 
    entry.do_entry_from_NONE(txt, TheState)

def side_entry_do(txt, TheState, TheAnalyzer):
    """Generate side entry to the init state, IF NECESSARY. An init state does
    not increment the input pointer at its first entry (when the function is
    entered). Other states, though, may enter the init state and then the input
    pointer must be incremented. This is solved by the construction:

       INIT_STATE_TRANSITION_BLOCK:
            ... transitions based on 'input' ...

       _xyz:           /* xyz = Init State Index  */
            ++input_p; /* Increment input pointer */
            goto INIT_STATE_TRANSITION_BLOCK;
    """
    global LanguageDB

    # Check whether the side entry is actually an issue for the given state
    if   not TheState.init_state_forward_f:              return
    elif not TheAnalyzer.has_transition_to_init_state(): return

    # Implement side entry: - increment input pointer 
    #                       - goto transition block.
    entry.do(txt, TheState, TheAnalyzer)
    txt.extend([
        "\n", 
        1, "%s\n" % LanguageDB.INPUT_P_INCREMENT(),
        1, "%s\n" % LanguageDB.GOTO_ADDRESS(get_address("$init_state_transition_block", TheState.index))
    ])
    return txt

def input_do(txt, TheState, TheAnalyzer, ForceInputDereferencingF=False):
    """Generate the code fragment that accesses the 'input' character for
       the subsequent transition map. In general this consists of 

            -- increment/decrement (if not init state forward)
            -- dereference the input pointer

       The initial state in forward lexing is an exception! The input pointer
       is not increased, since it already stands on the right position from
       the last analyzis step. When the init state is entered from any 'normal'
       state it enters via the 'epilog' generated in the function 
       non_default_init_state_entry().
    """
    LanguageDB = Setup.language_db
    action     = get_input_action(TheAnalyzer.engine_type, TheState, ForceInputDereferencingF)
    txt.append(1)
    LanguageDB.ACCESS_INPUT(txt, action, 1)
    txt.append(1)
    LanguageDB.STATE_DEBUG_INFO(txt, TheState)

def get_input_action(EngineType, TheState, ForceInputDereferencingF):
    action = EngineType.input_action(TheState.init_state_f)

    if TheState.transition_map_empty_f:
        # If the state has no further transitions then the input character does 
        # not have to be read. This is so, since without a transition map, the 
        # state immediately drops out. The drop out transits to a terminal. 
        # Then, the next action will happen from the init state where we work
        # on the same position. If required the reload happens at that moment.
        #
        # This is not true for Path Walker States, so we offer the option 
        # 'ForceInputDereferencingF'
        if not ForceInputDereferencingF:
            if   action == E_InputActions.INCREMENT_THEN_DEREF: return E_InputActions.INCREMENT
            elif action == E_InputActions.DECREMENT_THEN_DEREF: return E_InputActions.DECREMENT

    return action

