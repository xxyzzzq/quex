from   quex.blackboard                              import setup as Setup, E_StateIndices
from   quex.engine.generator.state.transition.code  import TextTransitionCode
from   quex.engine.analyzer.mega_state.core         import MegaState_Target
from   quex.engine.interval_handling                import Interval
from   quex.engine.generator.languages.address      import get_label
import quex.engine.generator.state.drop_out         as drop_out_coder
import sys

#class Handler:
#    def __init__(self, TheState):
#        self.force_input_dereferencing_f = False
#        if isinstance(TheState, PathWalkerState):
#            self.force_input_dereferencing_f = True
#            self.require_data = self.__path_walker_require_data
#        else:
#            self.require_data = self.__template_require_data
#
#
#def do(txt, TheState, TheAnalyzer):
#    LanguageDB = Setup.language_db
#
#    handler = Handler(TheState)
#
#    # (*) Entry _______________________________________________________________
#    entry_coder.do(txt, TheState, TheAnalyzer) 
#
#    # (*) Access input character ______________________________________________
#    input_do(txt, TheState, handler.force_input_dereferencing_f) 
#
#    # (*) MegaState specific frameworks
#    handler.framework(txt, TheState, TheAnalyzer)
#
#    # (*) Transition Map ______________________________________________________
#    prepare_transition_map(TheState)
#    transition_block.do(txt, 
#                        TheState.transition_map, 
#                        TheState.index, 
#                        TheState.engine_type, 
#                        TheState.init_state_f, 
#                        TheAnalyzer = TheAnalyzer)
#
#    # (*) Drop Out ____________________________________________________________
#    __drop_out(txt, TheState, TheAnalyzer)
#
#    # (*) Request necessary variable definition _______________________________
#    handler.require_data(TheState)
#
#    return

def drop_out_scheme_implementation(txt, TheState, TheAnalyzer, StateKeyString, DebugString):
    """DropOut Section:

       The drop out section is the place where we come if the transition map
       does not trigger to another state. We also land here if the reload fails.
       The routing to the different drop-outs of the related states happens by 
       means of a switch statement, e.g.
       
       _4711: /* Address of the drop out */
           switch( state_key ) {
           case 0:
                 ... drop out of state 815 ...
           case 1: 
                 ... drop out of state 541 ...
           }

       The switch statement is not necessary if all drop outs are the same, 
       of course.
    """
    LanguageDB = Setup.language_db
    # (*) Central Label for the Templates Drop Out
    #     (The rules for having or not having a label here are complicated, 
    #      so rely on the label's usage database.)
    txt.append("%s:\n" % get_label("$drop-out", TheState.index))
    txt.append("    %s\n" % DebugString) 

    # (*) Drop Out Section(s)
    if TheState.uniform_drop_outs_f:
        # -- uniform drop outs => no switch required
        prototype = TheAnalyzer.state_db[TheState.state_index_list[0]]
        tmp = []
        drop_out_coder.do(tmp, prototype, TheAnalyzer, DefineLabelF=False)
        txt.extend(tmp)
        return

    # -- non-uniform drop outs => route by 'state_key'
    case_list = []
    for drop_out, state_index_list in TheState.drop_out.iteritems():
        # state keys related to drop out
        state_key_list = map(lambda i: TheState.state_index_list.index(i), state_index_list)
        # drop out action
        assert len(state_index_list) != 0
        prototype = TheAnalyzer.state_db[state_index_list.__iter__().next()]
        action = []
        drop_out_coder.do(action, prototype, TheAnalyzer, DefineLabelF=False)
        case_list.append( (state_key_list, action) )

    case_txt = LanguageDB.SELECTION(StateKeyString, case_list)
    LanguageDB.INDENT(case_txt)
    txt.extend(case_txt)

def prepare_transition_map(TheState):
    """Prepare the transition map of the MegaState for code generation.

       NOTE: A word about the reload procedure.
       
       Reload can end either with success (new data has been loaded), or failure
       (no more data available). In case of success the **only** the transition
       step has to be repeated. Nothing else is effected.  Stored positions are
       adapted automatically.
       
       By convention we redo the transition map, in case of reload success and 
       jump to the state's drop-out in case of failure. There is no difference
       here in the template state example.
    """
    LanguageDB = Setup.language_db

    # Transition map of the 'skeleton'        
    if TheState.transition_map_empty_f:
        # Transition Map Empty:
        # This happens, for example, if there are only keywords and no 
        # 'overlaying' identifier pattern. But, in this case also, there
        # must be something that catches the 'buffer limit code'. 
        # => Define an 'all drop out' trigger_map, and then later
        # => Adapt the trigger map, so that the 'buffer limit' is an 
        #    isolated single interval.
        TheState.transition_map = [ (Interval(-sys.maxint, sys.maxint), MegaState_Target(E_StateIndices.DROP_OUT)) ]

    transition_map = TheState.transition_map

    for i, info in enumerate(transition_map):
        interval, target = info
        
        if   target.drop_out_f:
            # Later functions detect the 'DROP_OUT' in the transition map, so
            # we do not want to put it in text here. Namely function:
            # __separate_buffer_limit_code_transition(...) which implements the
            # buffer limit code insertion.
            transition_map[i] = (interval, E_StateIndices.DROP_OUT)
            continue

        if target.door_id is not None:
            text = LanguageDB.GOTO_BY_DOOR_ID(target.door_id)

        else:
            get_label("$state-router", U=True) # Ensure reference of state router
            # Transition target depends on state key
            label = "template_%i_target_%i[state_key]" % (TheState.index, target.index)
            text  = LanguageDB.GOTO_BY_VARIABLE(label)

        # Replace target 'i' by written text
        target            = TextTransitionCode([text])
        transition_map[i] = (interval, target)

    return

