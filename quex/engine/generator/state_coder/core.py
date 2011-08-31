from   quex.engine.analyzer.core import Analyzer, \
                                        AnalyzerState
from   quex.engine.state_machine.state_core_info          import E_EngineTypes, E_AcceptanceIDs
from   quex.engine.generator.languages.address            import Address
import quex.engine.generator.state_coder.transition_block as transition_block
import quex.engine.generator.state_coder.entry            as entry
import quex.engine.generator.state_coder.drop_out         as drop_out
from   quex.blackboard import E_StateIndices, \
                              setup as Setup

def do(txt, TheState, TheAnalyzer):
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    LanguageDB = Setup.language_db

    if TheState.init_state_forward_f:
        init_state_forward_entry(txt)
        transition_block_f = True
    else:
        transition_block_f = entry.do(txt, TheState, TheAnalyzer)

    if transition_block_f:
        input_do(txt, TheState)
        transition_block.do(txt, TheState.transition_map, TheState.index, TheState.engine_type, TheState.init_state_f)
        drop_out.do(txt, TheState, TheAnalyzer)

    if TheState.init_state_forward_f:
        init_state_forward_epilog(txt, TheState, TheAnalyzer)

    LanguageDB.REPLACE_INDENT(txt)

    for i, x in enumerate(txt):
        assert not isinstance(x, list), repr(txt[i-2:i+2])
        assert not x is None, txt[i-2:i+2]

def input_do(txt, TheState):
    """Generate the code fragment that accesses the 'input' character for
       the subsequent transition map. In general this consists of 

            -- increment/decrement (if not init state forward)
            -- dereference the input pointer

       The initial state in forward lexing is an exception! The input pointer
       is not increased, since it already stands on the right position from
       the last analyzis step. When the init state is entered from any 'normal'
       state it enters via the 'epilog' generated in the function 
       init_state_forward_epilog().
    """
    LanguageDB = Setup.language_db
    LanguageDB.ACCESS_INPUT(txt, TheState.input)

def init_state_forward_entry(txt):
    LanguageDB = Setup.language_db

    txt.append(LanguageDB.LABEL_INIT_STATE_TRANSITION_BLOCK())

def init_state_forward_epilog(txt, TheState, TheAnalyzer):
    assert TheState.init_state_forward_f

    LanguageDB = Setup.language_db

    entry.do(txt, TheState, TheAnalyzer)
    txt.extend([
        "\n", 
        "    ", LanguageDB.INPUT_P_INCREMENT,                                    "\n",
        "    ", LanguageDB.GOTO(E_StateIndices.INIT_STATE_TRANSITION_BLOCK), "\n",
    ])
    return txt
