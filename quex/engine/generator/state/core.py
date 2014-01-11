from   quex.engine.analyzer.core                    import Analyzer
from   quex.engine.analyzer.state.core              import AnalyzerState
from   quex.engine.generator.state.transition.code  import relate_to_TransitionCode
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.entry            as entry
import quex.engine.generator.state.drop_out         as drop_out
from   quex.engine.tools                            import none_isinstance, none_is_None
from   quex.blackboard                              import setup as Setup, E_InputActions

def do(code, TheState, TheAnalyzer):
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    # (*) Entry _______________________________________________________________
    txt, post_txt = entry.do(TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    tm = relate_to_TransitionCode(TheState.transition_map)
    transition_block.do(txt, tm)

    # (*) Drop Out ____________________________________________________________
    drop_out.do(txt, TheState.index, TheState.drop_out, TheAnalyzer)

    # ( ) Post-state entry to init state (if necessary)
    txt.extend(post_txt) 

    # (*) Consistency check ___________________________________________________
    assert none_isinstance(txt, list)
    assert none_is_None(txt)
    code.extend(txt)

