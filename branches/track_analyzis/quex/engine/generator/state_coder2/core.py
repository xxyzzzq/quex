from   quex.engine.analyzer.core import Analyzer, \
                                        AnalyzerState, \
                                        InputActions, \
                                        Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection
from   quex.engine.state_machine.state_core_info           import EngineTypes, AcceptanceIDs, PostContextIDs
from   quex.engine.generator.languages.address             import Address
import quex.engine.generator.state_coder2.transition_block as transition_block
import quex.engine.generator.state_coder2.entry            as entry
from   quex.blackboard import TargetStateIndices, \
                              setup as Setup
from   itertools import islice

def do(txt, TheState, TheAnalyzer):
    assert isinstance(TheState, AnalyzerState)
    assert isinstance(TheAnalyzer, Analyzer)

    LanguageDB = Setup.language_db

    if entry.do(txt, TheState, TheAnalyzer):
        input_do(txt, TheState)
        transition_block.do(txt, TheState)
        drop_out_do(txt, TheState, TheAnalyzer)

    epilog_if_init_state_do(txt, TheState)

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
       epilog_if_init_state_do().
    """
    LanguageDB = Setup.language_db
    LanguageDB.ACCESS_INPUT(txt, TheState.input)

def drop_out_do(txt, TheState, TheAnalyzer):
    LanguageDB          = Setup.language_db
    PositionRegisterMap = TheAnalyzer.position_register_map

    txt.append(Address("$drop-out", TheState.index))

    if TheState.engine_type == EngineTypes.BACKWARD_PRE_CONTEXT:
        txt.append("    %s\n" % LanguageDB.GOTO(TargetStateIndices.END_OF_PRE_CONTEXT_CHECK))
        return

    elif TheState.engine_type == EngineTypes.BACKWARD_INPUT_POSITION:
        txt.append("    %s\n" % LanguageDB.UNREACHABLE)
        return

    info = TheState.drop_out.trivialize()
    # (1) Trivial Solution
    if info is not None:
        for i, easy in enumerate(info):
            positioning_str = ""
            if easy[1].positioning != 0:
                if easy[1].positioning is None: register = PositionRegisterMap[easy[1].post_context_id]
                else:                           register = None
                positioning_str = "%s\n" % LanguageDB.POSITIONING(easy[1].positioning, register)

            goto_terminal_str = "%s" % LanguageDB.GOTO_TERMINAL(easy[1].acceptance_id)
            txt.append(LanguageDB.IF_PRE_CONTEXT(i == 0, easy[0].pre_context_id, 
                                                 "%s%s" % (positioning_str, goto_terminal_str)))
        return

    # (2) Separate: Pre-Context Check and Routing to Terminal
    # (2.1) Pre-Context Check
    for i, element in enumerate(TheState.drop_out.checker):
        if element.pre_context_id is None and element.acceptance_id == AcceptanceIDs.VOID: break
        txt.append(
            LanguageDB.IF_PRE_CONTEXT(i == 0, element.pre_context_id, 
                                      LanguageDB.ASSIGN("last_acceptance", "%i" % element.acceptance_id)))
        if element.pre_context_id is None: break # No check after the unconditional acceptance

    # (2.2) Routing to Terminal
    # (2.2.1) If the positioning is the same for all entries (except the FAILURE)
    #         then, again, the routing may be simplified:
    #router    = TheState.drop_out.router
    #prototype = (router[0].positioning, router[0].post_context_id)
    #simple_f  = True
    #for element in islice(router, 1, None):
    #    if element.acceptance_id == AcceptanceIDs.FAILURE: continue
    #    if prototype != (element.positioning, element.post_context_id): 
    #        simple_f = False
    #        break

    #if simple_f:
    #    txt.append("    %s\n    %s\n" % 
    #               (LanguageDB.POSITIONING(element.positioning, element.post_context_id), 
    #                LanguageDB.GOTO_TERMINAL(AcceptanceIDs.VOID)))
    #else:
    case_list = []
    for element in TheState.drop_out.router:
        if element.positioning is None: register = PositionRegisterMap[element.post_context_id]
        else:                           register = None
        case_list.append((LanguageDB.ACCEPTANCE(element.acceptance_id), 
                          "%s %s" % \
                          (LanguageDB.POSITIONING(element.positioning, register),
                           LanguageDB.GOTO_TERMINAL(element.acceptance_id))))

    txt.extend(LanguageDB.SELECTION("last_acceptance", case_list))

def epilog_if_init_state_do(txt, TheState):
    LanguageDB = Setup.language_db

    if not TheState.init_state_forward_f: return 
    # NOTE: TheState.state_is_entered_f is not enough, for example the init state
    #       reload procedure, might rely on the init state label being defined.

    txt.extend([
        "\n", 
        Address("$entry", TheState.index),                                       "\n",
        "    ", LanguageDB.INPUT_P_INCREMENT,                                    "\n",
        "    ", LanguageDB.GOTO(TargetStateIndices.INIT_STATE_TRANSITION_BLOCK), "\n",
    ])
    return txt
