from   quex.blackboard                                   import setup as Setup
from   quex.engine.analyzer.mega_state.template.state    import TemplateState
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
from   quex.engine.analyzer.mega_state.core              import MegaState_Target_DROP_OUT
from   quex.engine.analyzer.transition_map               import TransitionMap
from   quex.engine.generator.state.transition.code       import TransitionCodeFactory, \
                                                                MegaStateTransitionCodeFactory
import quex.engine.generator.state.transition.core  as     transition_block
import quex.engine.generator.state.drop_out         as     drop_out_coder
import quex.engine.generator.state.entry            as     entry_coder
import quex.engine.generator.mega_state.template    as     template
import quex.engine.generator.mega_state.path_walker as     path_walker
from   quex.engine.generator.languages.address      import get_label
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
        for state_index in self.state.state_index_sequence()[:-1]:
            state_key = self.state.map_state_index_to_state_key(state_index)
            txt.append("             (X) == %i ? %i :    \\\n" % (state_key, state_index))

        state_index = self.state.state_index_sequence()[-1]
        state_key   = self.state.map_state_index_to_state_key(state_index)
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
    entry_coder.do(txt, TheState, TheAnalyzer) 

    # (*) Access input character etc. _________________________________________
    specific.framework(txt, TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    tm = prepare_transition_map(TheState, TheAnalyzer, specific.state_key_str)
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
    LanguageDB = Setup.language_db
    # (*) Central Label for the Templates Drop Out
    #     (The rules for having or not having a label here are complicated, 
    #      so rely on the label's usage database.)
    txt.append("%s:\n" % get_label("$drop-out", TheState.index))
    txt.append("    %s\n" % DebugString) 

    uniform_drop_out = TheState.drop_out.get_uniform_prototype()

    # (*) Drop Out Section(s)
    if uniform_drop_out is not None:
        # uniform drop outs => no 'switch-case' required
        drop_out_coder.do(txt, TheState.index, uniform_drop_out, TheAnalyzer, \
                          DefineLabelF=False, MentionStateIndexF=False)
    else:
        # non-uniform drop outs => route by 'state_key'
        case_list = []
        for drop_out, state_index_set in TheState.drop_out.iteritems():
            # state keys related to drop out
            state_key_list = map(lambda i: TheState.map_state_index_to_state_key(i), state_index_set)
            # drop out action
            # Implement drop-out for each state key. 'state_key_list' combines
            # states that implement the same drop-out behavior. Same drop-outs
            # are implemented only once.
            case_txt = []
            drop_out_coder.do(case_txt, TheState.index, drop_out, TheAnalyzer, 
                              DefineLabelF=False, MentionStateIndexF=False)
            case_list.append((state_key_list, case_txt))

        case_txt = LanguageDB.SELECTION(StateKeyString, case_list)
        LanguageDB.INDENT(case_txt)
        txt.extend(case_txt)

def prepare_transition_map(TheState, TheAnalyzer, StateKeyStr):
    """Generate targets in the transition map which the code generation can 
       handle. The transition map will consist of pairs of
    
                          (Interval, TransitionCode)
    
       objects. 

       NOTE: A word about the reload procedure.
       
       Reload can end either with success (new data has been loaded), or failure
       (no more data available). In case of success the **only** the transition
       step has to be repeated. Nothing else is effected.  Stored positions are
       adapted automatically.
       
       By convention we redo the transition map, in case of reload success and 
       jump to the state's drop-out in case of failure. There is no difference
       here in the template state example.
    """
    # Transition map of the 'skeleton'        
    if TheState.transition_map_empty_f:
        # Transition Map Empty:
        # This happens, for example, if there are only keywords and no 
        # 'overlaying' identifier pattern. But, in this case also, there
        # must be something that catches the 'buffer limit code'. 
        # => Define an 'all drop out' trigger_map, and then later
        # => Adapt the trigger map, so that the 'buffer limit' is an 
        #    isolated single interval.
        TheState.transition_map = TransitionMap.from_iterable( 
            (Interval(-sys.maxint, sys.maxint), MegaState_Target_DROP_OUT) 
        )

    goto_reload_str = TransitionCodeFactory.prepare_reload_tansition(
                                 TM            = TheState.transition_map,
                                 StateIndex    = TheState.index,
                                 EngineType    = TheAnalyzer.engine_type,
                                 InitStateF    = TheState.init_state_f)

    MegaStateTransitionCodeFactory.init(TheState, TheAnalyzer.state_db, StateKeyStr, 
                                        TheAnalyzer.engine_type, goto_reload_str)

    return TransitionMap.from_iterable(TheState.transition_map, 
                                       MegaStateTransitionCodeFactory.do)

