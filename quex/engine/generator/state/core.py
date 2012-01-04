from   quex.engine.analyzer.core import Analyzer, \
                                        AnalyzerState
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.entry            as entry
import quex.engine.generator.state.drop_out         as drop_out
from   quex.blackboard import E_StateIndices, \
                              E_InputActions, \
                              setup as Setup

LanguageDB = None

def do(code, TheState, TheAnalyzer):
    global LanguageDB
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    LanguageDB = Setup.language_db
    txt        = []

    # (*) Entry _______________________________________________________________
    if not TheState.init_state_forward_f:
        entry.do(txt, TheState, TheAnalyzer)

    # (*) Access the triggering character _____________________________________
    #     There is something special about the init state in forward direction:
    #     It does not increment the input pointer initially. But when it is entered
    #     from other states, is has to do so. Solution: Implement init state entry
    #     as 'prologue' here (without increment) and epilogue (with increment) after 
    #     the state. 
    if TheState.init_state_forward_f:
        txt.append(LanguageDB.LABEL_INIT_STATE_TRANSITION_BLOCK())
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

def input_do(txt, TheState, ForceInputDereferencingF=False):
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
    global LanguageDB

    input = TheState.input
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
            if   input == E_InputActions.INCREMENT_THEN_DEREF: input = E_InputActions.INCREMENT
            elif input == E_InputActions.DECREMENT_THEN_DEREF: input = E_InputActions.DECREMENT
    LanguageDB.ACCESS_INPUT(txt, input)

def init_state_forward_entry(txt, TheState):
    global LanguageDB

    entry._accepter(txt, TheState.entry.get_accepter())

def init_state_forward_epilog(txt, TheState, TheAnalyzer):
    assert TheState.init_state_forward_f

    global LanguageDB

    entry.do(txt, TheState, TheAnalyzer)
    txt.extend([
        "\n", 
        "    %s\n" % LanguageDB.INPUT_P_INCREMENT(),
        "    %s\n" % LanguageDB.GOTO(E_StateIndices.INIT_STATE_TRANSITION_BLOCK),
    ])
    return txt
