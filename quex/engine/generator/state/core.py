from   quex.engine.analyzer.core                    import Analyzer
from   quex.engine.analyzer.state.core              import AnalyzerState
from   quex.engine.generator.state.transition.code  import relate_to_TransitionCode
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.entry            as entry
import quex.engine.generator.state.drop_out         as drop_out
from   quex.engine.generator.languages.address      import Label
from   quex.blackboard                              import setup as Setup, E_InputActions

LanguageDB = None

def do(code, TheState, TheAnalyzer):
    global LanguageDB
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    LanguageDB = Setup.language_db
    txt        = []

    # (*) Entry _______________________________________________________________
    entry.do_pre(txt, TheState, TheAnalyzer)

    # (*) Access the triggering character _____________________________________
    input_do(txt, TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    tm = relate_to_TransitionCode(TheState.transition_map)
    transition_block.do(txt, tm)

    # (*) Drop Out ____________________________________________________________
    drop_out.do(txt, TheState.index, TheState.drop_out, TheAnalyzer)

    # ( ) Post-state entry to init state (if necessary)
    entry.do_post(txt, TheState, TheAnalyzer)

    # (*) Cleaning Up _________________________________________________________
    for i, x in enumerate(txt):
        assert not isinstance(x, list), repr(txt[i-2:i+2])
        assert not x is None, txt[i-2:i+2]

    code.extend(txt)

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
    action     = get_input_action(TheAnalyzer, TheState, ForceInputDereferencingF)
    txt.append(1)
    LanguageDB.ACCESS_INPUT(txt, action, 1)
    txt.append(1)
    LanguageDB.STATE_DEBUG_INFO(txt, TheState, TheAnalyzer)

