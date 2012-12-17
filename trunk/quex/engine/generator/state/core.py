from   quex.engine.analyzer.core       import Analyzer
from   quex.engine.analyzer.state.core import AnalyzerState, \
                                              get_input_action
import quex.engine.analyzer.engine_supply_factory   as     engine
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.entry            as entry
import quex.engine.generator.state.drop_out         as drop_out
from   quex.blackboard import E_StateIndices, \
                              setup as Setup

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
    transition_block.do(txt, 
                        TheState.transition_map, 
                        TheState.index, 
                        TheState.engine_type, 
                        TheState.init_state_f, 
                        TheAnalyzer=TheAnalyzer)

    # (*) Drop Out ____________________________________________________________
    drop_out.do(txt, TheState, TheAnalyzer)

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
    # the LABEL_INIT_STATE_TRANSITION_BLOCK from there.
    if TheAnalyzer.has_transition_to_init_state():
        txt.append(LanguageDB.LABEL_INIT_STATE_TRANSITION_BLOCK())
    else:
        # Simply nothing required, not even a label.
        return

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
        1, "%s\n" % LanguageDB.GOTO(E_StateIndices.INIT_STATE_TRANSITION_BLOCK),
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

