from   quex.engine.generator.state.transition_map.code  import relate_to_TransitionCode
import quex.engine.generator.state.transition_map.core  as     transition_block
import quex.engine.generator.state.entry                as     entry
from   quex.engine.analyzer.core                        import Analyzer
from   quex.engine.analyzer.state.core                  import AnalyzerState
from   quex.engine.tools                                import none_isinstance, \
                                                               none_is_None

def do(code, TheState, TheAnalyzer):
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    # (*) Entry _______________________________________________________________
    txt, post_txt = entry.do(TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    tm = relate_to_TransitionCode(TheState.transition_map)
    transition_block.do(txt, tm)

    # ( ) Post-state entry to init state (if necessary)
    txt.extend(post_txt) 

    # (*) Consistency check ___________________________________________________
    assert none_isinstance(txt, list)
    assert none_is_None(txt)
    code.extend(txt)

