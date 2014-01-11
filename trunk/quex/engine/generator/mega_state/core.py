from   quex.blackboard                                   import Lng
from   quex.engine.analyzer.mega_state.template.state    import TemplateState
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
from   quex.engine.analyzer.transition_map               import TransitionMap
from   quex.engine.analyzer.door_id_address_label        import DoorID, IfDoorIdReferencedLabel
from   quex.engine.generator.state.transition.code       import TransitionCodeFactory, \
                                                                MegaState_relate_to_transition_code
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.drop_out         as     drop_out
import quex.engine.generator.state.entry            as     entry_coder
import quex.engine.generator.mega_state.template    as     template
import quex.engine.generator.mega_state.path_walker as     path_walker
from   quex.engine.interval_handling                import Interval
import sys

class Handler:
    def __init__(self, TheState):
        if isinstance(TheState, PathWalkerState):
            self.require_data = path_walker.require_data
            self.framework    = path_walker.framework   
            self.state_key_str      = "path_iterator - path_walker_%s_path_base" % TheState.index 
            self.debug_drop_out_str = "__quex_debug_path_walker_drop_out(%i, path_walker_%s_path_base, path_iterator);\n" \
                                      % (TheState.index, TheState.index)
        elif isinstance(TheState, TemplateState):
            self.require_data = template.require_data
            self.framework    = template.framework   
            self.state_key_str      = "state_key"
            self.debug_drop_out_str = "__quex_debug_template_drop_out(%i, state_key);\n" % TheState.index
        else:
            assert False

        self.state = TheState

    def debug_info_map_state_key_to_state_index(self, txt):
        txt.append("#   define __QUEX_DEBUG_MAP_STATE_KEY_TO_STATE(X) ( \\\n")
        pair_list = list((self.state.map_state_index_to_state_key(si), si) \
                         for si in self.state.implemented_state_index_set())
        pair_list.sort()
        for state_key, state_index in pair_list[:-1]:
            txt.append("             (X) == %i ? %i :    \\\n" % (state_key, state_index))

        state_index, state_index = pair_list[-1]
        txt.append("             (X) == %i ? %i : 0)" % (state_key, state_index))

        if isinstance(self.state, PathWalkerState):
            txt.append("\n#   define __QUEX_DEBUG_MAP_PATH_BASE_TO_PATH_ID(PB) ( \\\n")
            for path_id in xrange(len(self.state.path_list) - 1):
                txt.append("             (PB) == path_walker_%i_path_%i ? %i :    \\\n" \
                           % (self.state.index, path_id, path_id))
            path_id = len(self.state.path_list) - 1
            txt.append("             (PB) == path_walker_%i_path_%i ? %i : 0)" \
                       % (self.state.index, path_id, path_id))

    def debug_info_undo_map_state_key_to_state_index(self, txt):
        txt.append("\n#   undef __QUEX_DEBUG_MAP_STATE_KEY_TO_STATE\n")
        if isinstance(self.state, PathWalkerState):
            txt.append("#   undef __QUEX_DEBUG_MAP_PATH_BASE_TO_PATH_ID\n")

def do(txt, TheState, TheAnalyzer):
    specific = Handler(TheState)

    specific.debug_info_map_state_key_to_state_index(txt)

    # (*) Entry _______________________________________________________________
    pre_txt, post_txt = entry_coder.do(TheState, TheAnalyzer) 
    txt.extend(pre_txt)
    assert len(post_txt) == 0

    # (*) Access input character etc. _________________________________________
    specific.framework(txt, TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    tm = MegaState_relate_to_transition_code(TheState, TheAnalyzer, specific.state_key_str)
    transition_block.do(txt, tm)

    # (*) Drop Out ____________________________________________________________
    drop_out_scheme_do(txt, TheState, TheAnalyzer, 
                       specific.state_key_str, 
                       specific.debug_drop_out_str)

    # (*) Request necessary variable definition _______________________________
    specific.require_data(TheState, TheAnalyzer)

    specific.debug_info_undo_map_state_key_to_state_index(txt)
    return

def drop_out_scheme_do(txt, TheState, TheAnalyzer, StateKeyString, DebugString):
    """DropOut Section:

       The drop out section is the place where we come if the transition map
       does not trigger to another state. We also land here if the reload fails.

       A 'DropOut' object is a dictionary which maps from a command list
       to the list of states which it represents, i.e.

           map:       CommandList --> state_index_set

       which means that in the expression
        
              for command_list, state_index_set in DropOut.iteritems():
                  ...

       all states with indices from 'state_index_set' implement the drop
       out as the given 'command_list'.

       There are two possible cases: 
       
       (1) All DropOut-s of the MegaState are the same (uniform). Then 
           nothing has to be distinguished. Simply implement the CommandList.

       (2) DropOut-s for states differ. Than the state key is used to 
           distinguish between the different drop out CommandList-s.
       
           _4711: /* Address of the drop out */
               switch( state_key ) {
               case 0:
                     ... drop out of state 815 ...
               case 1: 
                     ... drop out of state 541 ...
               }
    """
    
    # (*) Central Label for the Templates Drop Out
    #     (The rules for having or not having a label here are complicated, 
    #      so rely on the label's usage database.)
    txt.append(IfDoorIdReferencedLabel(DoorID.drop_out(TheState.index)))
    txt.append("    %s\n" % DebugString) 

    uniform_drop_out, state_index_set = TheState.drop_out.get_uniform_prototype()

    # (*) Drop Out Section(s)
    if uniform_drop_out is not None:
        # uniform drop outs => no 'switch-case' required
        for state_index in state_index_set:
            txt.append(IfDoorIdReferencedLabel(DoorID.drop_out(state_index)))

        drop_out.do(txt, TheState.index, uniform_drop_out, TheAnalyzer, \
                    DefineLabelF=False, MentionStateIndexF=False)
    else:
        # There must be more than one drop-out scheme. Otherwise, it would be 
        # uniform.
        assert len(TheState.drop_out) > 1

        # non-uniform drop outs => route by 'state_key'
        case_list = []
        assert_remainder = set( 
            TheState.map_state_index_to_state_key(state_index)
            for state_index in TheState.implemented_state_index_set() 
        )

        for drop_out_object, state_index_set in TheState.drop_out.iteritems():
            # state keys related to drop out
            state_key_list = map(lambda i: TheState.map_state_index_to_state_key(i), state_index_set)
            assert assert_remainder.issuperset(state_key_list)
            assert_remainder.difference_update(state_key_list)

            # drop out action
            # Implement drop-out for each state key. 'state_key_list' combines
            # states that implement the same drop-out behavior. Same drop-outs
            # are implemented only once.
            case_txt = []
            for state_index in state_index_set:
                case_txt.append(IfDoorIdReferencedLabel(DoorID.drop_out(state_index)))
            drop_out.do(case_txt, TheState.index, drop_out_object, TheAnalyzer, 
                        DefineLabelF=False, MentionStateIndexF=False)
            case_list.append((state_key_list, case_txt))
    
        assert len(assert_remainder) == 0, "Missing: '%s'" % assert_remainder

        case_txt = Lng.SELECTION(StateKeyString, case_list)
        Lng.INDENT(case_txt)
        txt.extend(case_txt)

