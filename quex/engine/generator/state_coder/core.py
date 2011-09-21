from   quex.engine.analyzer.core import Analyzer, \
                                        AnalyzerState
from   quex.engine.generator.languages.address            import Address
import quex.engine.generator.state_coder.transition_block as transition_block
import quex.engine.generator.state_coder.entry            as entry
import quex.engine.generator.state_coder.drop_out         as drop_out
from   quex.blackboard import E_StateIndices, \
                              E_EngineTypes, E_AcceptanceIDs, \
                              setup as Setup

def do(code, TheState, TheAnalyzer):
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    LanguageDB = Setup.language_db
    txt        = []

    # (*) Entry _______________________________________________________________
    #     There is something special about the init state in forward direction:
    #     It does not increment the input pointer initially. But when it is entered
    #     from other states, is has to do so. Solution: Implement init state entry
    #     as 'prologue' here (without increment) and epilogue (with increment) after 
    #     the state. 
    if TheState.init_state_forward_f: init_state_forward_entry(txt, TheState)
    else:                             entry.do(txt, TheState, TheAnalyzer)

    # (*) Access the triggering character _____________________________________
    input_do(txt, TheState)

    # (*) Transition Map ______________________________________________________
    transition_block.do(txt, 
                        TheState.transition_map, 
                        TheState.index, 
                        TheState.engine_type, 
                        TheState.init_state_f, 
                        TheAnalyzer=TheAnalyzer)

    # (*) Drop Out ____________________________________________________________
    drop_out.do(txt, TheState, TheAnalyzer)

    # ( ) Init state prologue (if necessary)
    if TheState.init_state_forward_f:
        init_state_forward_epilog(txt, TheState, TheAnalyzer)

    # (*) Cleaning Up _________________________________________________________
    for i, x in enumerate(txt):
        assert not isinstance(x, list), repr(txt[i-2:i+2])
        assert not x is None, txt[i-2:i+2]

    code.extend(txt)

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

def init_state_forward_entry(txt, TheState):
    LanguageDB = Setup.language_db

    LanguageDB.STATE_DEBUG_INFO(txt, TheState)
    entry._accepter(txt, TheState.entry.get_accepter())
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
