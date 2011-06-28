from   quex.engine.analyzer.core import AnalyzerState, \
                                        InputActions
from   quex.engine.state_machine.state_core_info           import EngineTypes
import quex.engine.generator.state_coder2.transition_block as transition_block

def do(txt, TheState):
    assert isinstance(TheState, AnalyzerState)

    do_input(txt, TheState)
    do_entry(txt, TheState)
    transition_block.do(txt, TheState)
    do_drop_out(txt. TheState)
    do_epilog_if_init_state(txt, TheState)

def do_input(txt, TheState):
    """Generate the code fragment that accesses the 'input' character for
       the subsequent transition map. In general this consists of 

       The initial state in forward lexing is an exception! The input pointer
       is not increased, since it already stands on the right position from
       the last analyzis step. When the init state is entered from any 'normal'
       state it enters via the 'epilog' generated in the function 
       do_epilog_if_init_state().
    """
    LanguageDB = Setup.language_db

    txt.append(LanguageDB(STATE_ENTRY(TheState)))
    txt.append(LanguageDB.ACCESS_INPUT(TheState.input))

    return

def do_entry(txt, TheState):

    if isinstance(TheState.entry, Entry):
        accepter = self.get_accepter()
        if len(accepter) != 0:
            first_f = True
            for pre_context_id, acceptance_id in TheState.get_accepter():
                assert isinstance(acceptance_id, (int, long))
                txt.append(
                    LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                              LanguageDB.ASSIGN("last_acceptance", "%i" % acceptance_id))
                )
                first_f = False
            LanguageDB.END_IF(first_f)

        if len(self.positioner) != 0:
            first_f = True
            for position_register, pre_context_id_list in TheState.get_positioner():
                txt.append(
                    LanguageDB.IF_PRE_CONTEXT(first_f, pre_context_id_list, 
                                              LanguageDB.ASSIGN("position[%i]" % position_register, "input_p")), 
                )
                first_f = False
            LanguageDB.END_IF(first_f)
            
    elif isinstance(TheState.entry, EntryBackward):
        for pre_context_id in TheState.entry.pre_context_fulfilled_set:
            txt.append(LanguageDB.ASSIGN("pre_context_%i_fulfilled_f" % pre_context_id, "true"))

    elif isinstance(TheState.entry, EntryBackwardInputPositionDetection):
        if TheState.entry.terminated_f: 
            txt.append("    %s\n" % LanguageDB.RETURN)

def do_drop_out(txt, TheState):

    if TheState.engine_type == EngineTypes.BACKWARD:
        txt.append("    %s\n" % LanguageDB.GOTO(StateIndices.END_OF_PRE_CONTEXT_CHECK)

    elif TheState.engine_type == EngineTypes.BACKWARD_INPUT_POSITION:
        txt.append("    %s\n" % LanguageDB.UNREACHABLE)

    info = self.trivialize()
    if info is not None:
        first_f = True
        for easy in info:
            txt.append(
                LanguageDB.IF_PRE_CONTEXT(first_f, easy[0].pre_context_id, 
                                          "    %s\n    %s\n" % \
                                          (LanguageDB.POSITIONING(easy[1].positioning, easy[1].post_context_id)
                                           LanguageDB.GOTO_TERMINAL(easy[1].acceptance_id)))
            )

            first_f = False
        return

    first_f = True
    for element in self.checker:
        txt.append("        ")
        txt.append(
            LanguageDB.IF_PRE_CONTEXT(first_f, element.pre_context_id, 
                                      LanguageDB.ASSIGN("last_acceptance", "%i" element.acceptance_id))
        )
        txt.append("\n")
        if element.pre_context_id is None: break # No check after the unconditional acceptance
        first_f = False

    case_list = []
    for element in self.router:
        if element.acceptance_id == AcceptanceIDs.FAILURE: assert self.positioning == -1 
        else:                                              assert self.positioning != -1

        if element.positioning != 0:
            case_list.append((element.acceptance_id, 
                              "%s %s" % \
                              (LanguageDB.POSITION(element.positioning, element.post_context_id), 
                               LanguageDB.GOTO_TERMINAL(element.acceptance_id)))
        else:
            case_list.append((element.acceptance_id, 
                              LanguageDB.GOTO_TERMINAL(element.acceptance_id)))

    txt.append(LanguageDB.SELECTION(case_list))

def do_epilog_if_init_state(txt, TheState)
    LanguageDB = Setup.language_db
    if not TheState.init_state_f:       return 
    if not TheState.state_is_entered_f: return

    txt.extend([
        "\n", 
        Address("$entry", StateIdx),            "\n",
        "    ", LanguageDB["$input/increment"], "\n",
        "    ", LanguageDB.GOTO(StateIndices.INIT_STATE_TRANSITION_BLOCK), "\n"
    ])
    return txt
