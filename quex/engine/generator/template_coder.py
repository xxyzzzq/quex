# (C) 2009-2011 Frank-Rene Schaefer
import quex.engine.generator.state_coder.transition_block as transition_block
from   quex.engine.generator.state_coder.transition_code  import TransitionCode, TextTransitionCode
import quex.engine.generator.state_coder.drop_out         as drop_out_coder
import quex.engine.generator.state_coder.entry            as entry_coder
from   quex.engine.generator.state_coder.core             import input_do
from   quex.engine.generator.languages.address            import get_address, get_label, get_label_of_address
from   quex.engine.generator.languages.variable_db        import variable_db
import quex.engine.state_machine.index                    as     index
from   quex.engine.analyzer.core                          import AnalyzerState
import quex.engine.state_machine.core                     as     state_machine

import quex.engine.analyzer.template.core                 as templates 

from   copy            import deepcopy
from   quex.blackboard import setup as Setup, E_StateIndices
from   itertools       import imap
from   operator        import attrgetter

"""Template Compression _______________________________________________________

   Consider the file 'analyzer/template/core.py' for a detailed explanation of 
   template compression.

   Code Generation ____________________________________________________________

   If there is a template consisting of a (adaptable) transition map such as 

                    [0, 32)    -> drop 
                    [32]       -> Target0  
                    [33, 64)   -> 721
                    [64, 103)  -> Target1
                    [103, 255) -> Target2

   where Target0, Target1, and Target2 are defined dependent on the involved
   states 4711, 2123, and 8912 as

                        4711   3123  8912
              Target0:   891   drop   213   
              Target1:   718   718    721
              Target2:   718   drop   711

   Then, the code generator need to create:

     (1) Transition Target Data Structures: 

             Target0 = { 891, 718, 718 };
             Target1 = {  -1, 718,  -1 };
             Target2 = { 213, 721, 711 };

         There might be multiple templates, so actually 'Target0' must be
         implemented as 'Template66_Target0' if the current template is '66'.
         The above writing is chosen for simplicity.

    (2) Templated State Entries:

            STATE_4711: 
               key = 0; goto TEMPLATE_STATE_111;
            STATE_3123: 
               key = 1; goto TEMPLATE_STATE_111;
            STATE_8912: 
               key = 2; goto TEMPLATE_STATE_111;

        this way the 'gotos' to templated states remain identical to the gotos
        of non-templated states. The 'key' lets the template behave according
        to a particular state.

    (3) Templated State (with its transition map, etc.):

            STATE_111: 
              input = get();

              if input in [0, 32)    then drop 
              if input in [32]       then Target0[key]  
              if input in [33, 64)   then 721          
              if input in [64, 103)  then Target1[key]
              if input in [103, 255) then Target2[key]

              ...

         The key is basically the index in the involved state list, e.g. '0' is
         the key for state '4711' above, '1' is the key for state '3123' and
         '2' is the key for '8912'.

    (4) State Router:
    
        A state router, all states in the target maps must be map-able if no
        computed goto is used.
        
            switch( state_index ) {
            case 4711: goto STATE_4711;
            case 3214: goto STATE_3214;
            ...
            }
"""
LanguageDB = None # Set during call to 'do()', not earlier

def do(txt, TheAnalyzer, MinGain):
    """Tries to combine as many states as possible from TheAnalyzer
       into TemplateState-s. It uses an iterative stepwise algorithm
       were at each step two states are combined as long as the 
       gain is above a given minimum 'MinGain.'

       Generated code is written into the array 'txt'. The scheme of
       code generation for a TemplateState follows the scheme of 
       'state_coder/core.py' for AnalyzerState-s and is implemented
       in function 'state_coder_do()'.
    
       RETURNS: 

       'Done List', i.e. a list of indices of states which have been 
                    combined into template states.
    """
    global LanguageDB
    LanguageDB = Setup.language_db

    # (*) Analysis:
    #     Determine TemplateState-s as combinations of AnalyzerState-s.
    template_state_list = templates.do(TheAnalyzer, MinGain)

    if len(template_state_list) == 0: return []

    # (*) Code Generation:
    variable_db.require("template_state_key")

    done_list = set([])
    for t_state in template_state_list:
        state_coder_do(txt, t_state, TheAnalyzer)
        done_list.update(t_state.state_index_list)

    return done_list

def state_coder_do(txt, TState, TheAnalyzer):
    """Generate code for given template state 'TState'. This follows the 
       scheme of code generation for AnalyzerState-s in 'state_coder/core.py'.
    """
    # (*) Entry _______________________________________________________________
    __entry(txt, TState, TheAnalyzer)

    # (*) Access input character ______________________________________________
    input_do(txt, TState) 

    # (*) Transition Map ______________________________________________________
    __transition_map(txt, TState, TheAnalyzer)

    # (*) Drop Out ____________________________________________________________
    __drop_out(txt, TState, TheAnalyzer)

    # (*) Request necessary variable definition _______________________________
    __require_target_scheme_data(TState, TheAnalyzer)

    return 

def __entry(txt, TState, TheAnalyzer):
    """Entry of a template state. Three main cases:

       (1) Entries of involved states are all the same.
     
           /* Labels for states (targeted by 'goto-s') */
           _1575: template_state_key = 0;  goto _4711;
           _1212: template_state_key = 1;  goto _4711;
           ...
           _1312: template_state_key = 41; goto _4711;

           /* Common Entry */
           _4711: 
              ...

       (2) Entries of involved states are different:
           
           (2.i) An entry is the same for multiple states
               
                 Same as case (1), but at the end of the common 
                 entry:

                 goto 'TemplateBody'.

           (2.ii) Each state has its own entry, then assign the
                  template_state_key immediately after each state's
                  entry. Then, 

                 goto 'TemplateBody'.
    """
    global LanguageDB
    def help(StateIndexList):
        return imap(lambda i: 
                    (i, TState.state_index_list.index(i), TheAnalyzer.state_db[i]), 
                    StateIndexList)

    if TState.uniform_entries_f:
        entry, state_index_list = TState.entry.iteritems().next()
        # Assign the state keys for each state involved
        for state_index, state_key, state in help(state_index_list): 
            LanguageDB.STATE_ENTRY(txt, state)
            txt.append("    %s\n" % LanguageDB.ASSIGN("template_state_key", "%i" % state_key))
            txt.append("    %s\n" % LanguageDB.GOTO(TState.index))

        # Implement the common entry
        txt.extend("%s\n" % LanguageDB.LABEL(TState.index))
        entry_coder.do(txt, TState, TheAnalyzer, UnreachablePrefixF=False, LabelF=False)
        return

    # Non-Uniform Entries
    i = -1
    for entry, state_index_list in TState.entry.iteritems():
        if entry.is_independent_of_source_state():
            i += 1
            # Assign the state keys for each state involved
            for state_index, state_key, state in help(state_index_list): 
                LanguageDB.STATE_ENTRY(txt, state)
                txt.append("    %s\n" % LanguageDB.ASSIGN("template_state_key", "%i" % state_key))
                if len(state_index_list) != 1:
                    txt.append("    %s\n" % LanguageDB.GOTO_TEMPLATE_ENTRY(TState.index, i))
            # Implement the common entry
            if len(state_index_list) != 1:
                txt.extend("%s\n" % LanguageDB.LABEL_TEMPLATE_ENTRY(TState.index, i))
            prototype = TheAnalyzer.state_db[state_index_list[0]]
            entry_coder.do(txt, prototype, TheAnalyzer, UnreachablePrefixF=False, LabelF=False)
            txt.append("    %s\n" % LanguageDB.GOTO(TState.index))
        else:
            for state_index, state_key, state in help(state_index_list): 
                # Implement the particular entry
                tmp = []
                entry_coder.do(tmp, state, TheAnalyzer) # , UnreachablePrefixF=(i==0))
                txt.extend(tmp)
                # Assign the state keys for each state involved
                txt.append("    %s\n" % LanguageDB.ASSIGN("template_state_key", "%i" % state_key))
                txt.append("    %s\n" % LanguageDB.GOTO(TState.index))

    # Implement entry point
    txt.extend("%s\n" % LanguageDB.LABEL(TState.index))

def __transition_map(txt, TState, TheAnalyzer):
    """Generates code for transition map of a template state."""

    replace_TargetScheme_by_TemplateTransitionCode(TState, TheAnalyzer)
    on_reload_ok_str, on_reload_fail_str = get_reload_info(TState)

    transition_block.do(txt, 
                        TState.transition_map, 
                        TState.index, 
                        TState.engine_type, 
                        TState.init_state_f, 
                        OnReloadOK_Str   = on_reload_ok_str,
                        OnReloadFail_Str = on_reload_fail_str,
                        TheAnalyzer      = TheAnalyzer)

def __drop_out(txt, TState, TheAnalyzer):
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
    # (*) Central Label for the Templates Drop Out
    txt.append("%s:\n" % get_label("$drop-out", TState.index, U=True, R=True))

    # (*) Drop Out Section(s)
    if TState.uniform_drop_outs_f:
        # -- uniform drop outs => no switch required
        prototype = TheAnalyzer.state_db[TState.state_index_list[0]]
        drop_out_coder.do(txt, prototype, TheAnalyzer, DefineLabelF=False)
        return

    # -- non-uniform drop outs => route by 'state_key'
    case_list = []
    for drop_out, state_index_list in TState.drop_out.iteritems():
        # state keys related to drop out
        state_key_list = map(lambda i: TState.state_index_list.index(i), state_index_list)
        # drop out action
        prototype = TheAnalyzer.state_db[state_index_list[0]]
        action = []
        drop_out_coder.do(action, prototype, TheAnalyzer, DefineLabelF=False)
        case_list.append( (state_key_list, action) )

    case_txt = LanguageDB.SELECTION("template_state_key", case_list)
    LanguageDB.INDENT(case_txt)
    txt.extend(case_txt)

class TemplateTransitionCode(TransitionCode):
    """A transition in a template state's transition map may depend on 
       a given state_key. The relation what state is targeted for what
       state key is coded in a TargetScheme. 

       A TemplateTransitionCode tells how the TargetScheme is implemented
       in code, i.e. how to implement a transition for a given template
       state and a given state_key.
       
       It is derived from TransitionCode, so that it fits the code generation
       of 'transition_block.py'.
    """
    def __init__(self, TState, TargetSchemeIndex):
        self.template_index      = TState.index
        self.target_scheme_index = TargetSchemeIndex
        self.__uniform_entries_f = TState.uniform_entries_f

        TransitionCode.__init__(self, 
                                Target=None, 
                                StateIndex=TState.index,
                                InitStateF=False, 
                                EngineType=TState.engine_type, 
                                OnReloadOK_Str=None, 
                                GotoReload_Str=None, 
                                OnReloadFail_Str=None, 
                                TheAnalyzer=None)

    def __eq__(self, Other):
        """Equal/Not Equal comparison operators are required for effective 
           transition code generation.
        """
        if Other.__class__ != TemplateTransitionCode: return False
        return     self.template_index            == Other.template_index \
               and self.target_scheme_index       == Other.target_scheme_index \
               and self.__uniform_entries_f == Other.__uniform_entries_f

    def __ne__(self, Other):
        return not self.__eq__(Other)

    @property
    def code(self):
        """Template transition target states. The target state is determined at 
           run-time based on a 'state_key' for the template.
           NOTE: This handles also the recursive case.
        """
        if self.target_scheme_index != E_StateIndices.RECURSIVE:
            # (*) Normal Case: 
            #     Transition target depends on state key
            label = "template_%i_target_%i[template_state_key]" % (self.template_index, self.target_scheme_index)
            get_label("$state-router", U=True) # Ensure reference of state router
            return "QUEX_GOTO_STATE(%s);" % label 

        elif not self.__uniform_entries_f:
            # (*) Recursive Case 1:
            #     Jump to dedicated entry determined by 'state_key'.
            label = "template_%i_map_state_key_to_entry_index[template_state_key]" % self.template_index
            get_label("$state-router", U=True) # Ensure reference of state router
            return "QUEX_GOTO_STATE(%s);" % label 

        else:
            # (*) Recursive Case 2:
            #     All states have same entry, thus simply enter the template again.
            return "goto %s;" % get_label_of_address(self.template_index, U=True) 

    @property
    def drop_out_f(self): return False

def replace_TargetScheme_by_TemplateTransitionCode(TState, TheAnalyzer):
    """Prepare transition map for code generation:
    
       -- Replace TargetScheme objects by TemplateTransitionCode objects in transition map.

       -- If a target state that is **common** for all involved states has special doors
          for different source states, then implement a goto based on the state_key.

       NOTE: This is no contradiction to the restriction 'no target with source state 
             dependent entries.' The targets in the restrictions are targets of TargetSchemes,
             here we talk about common targets, i.e. 'a scalar value' in the transition map.
    """
    global LanguageDB
    
    for i, info in enumerate(TState.transition_map):
        interval, target_scheme = info
        if isinstance(target_scheme, (int, long)): 
            target_index = target_scheme
            entry = TheAnalyzer.state_db[target_index].entry
            if entry.is_independent_of_source_state(): continue
            case_list = []
            # A common target state of a template is targeted by all involved states.
            # => If the target state's entries depend on the source state all
            #    states in the template's state_index_list must be mentioned as entry.
            for state_key, from_state_index in enumerate(TState.state_index_list):
                if not entry.special_door_from_state(from_state_index): from_state_index = None
                case_list.append((state_key, LanguageDB.GOTO(target_index, from_state_index, TState.engine_type))) 
            code = LanguageDB.SELECTION("template_state_key", case_list)
            LanguageDB.INDENT(code, 2)
            target = TextTransitionCode(["\n"] + code)
        else:
            if   target_scheme == E_StateIndices.DROP_OUT:  continue
            elif target_scheme == E_StateIndices.RECURSIVE: scheme_index = E_StateIndices.RECURSIVE 
            else:                                           scheme_index = target_scheme.index
            target = TemplateTransitionCode(TState, scheme_index)

        TState.transition_map[i] = (interval, target)

    return 

def __require_target_scheme_data(TState, TheAnalyzer):
    """Defines the transition targets for each involved state.
    """
    def help(AdrList):
        return "".join(["{ "] + map(lambda adr: "QUEX_LABEL(%i), " % adr, AdrList) + [" }"])

    for target_scheme in sorted(TState.target_scheme_list, key=attrgetter("index")):
        assert len(target_scheme.scheme) == len(TState.state_index_list)
        address_list = []
        for state_key, target in enumerate(target_scheme.scheme):
            if target == E_StateIndices.DROP_OUT:
                elm = get_address("$drop-out", TState.index, U=True)
            else:
                # Quex's whole infrastructure does not allow to have target schemes where
                # we need to differentiate at state entries with respect to the source state.
                # It **must** be assumed that no transition map is generated that contains
                # target states that have different doors for different source states.
                assert TheAnalyzer.state_db[target].entry.is_independent_of_source_state()
                elm = get_address("$entry", target, U=True, R=True)

            address_list.append(elm)

        variable_db.require_array("template_%i_target_%i", 
                                  ElementN = len(TState.state_index_list), 
                                  Initial  = help(address_list),
                                  Index    = (TState.index, target_scheme.index))

    # If the template does not have uniform state entries, the entries
    # need to be routed on recursion, for example. Thus we need to map 
    # from state-key to state.
    if not TState.uniform_entries_f:
        address_list = map(lambda i: get_address("$entry", i, U=True, R=True), 
                           TState.state_index_list)
        variable_db.require_array("template_%i_map_state_key_to_entry_index", 
                                  ElementN = len(TState.state_index_list), 
                                  Initial  = help(address_list),
                                  Index    = TState.index)

    # Drop outs: all drop outs end up at the end of the transition map, where
    # it is routed via the state_key to the state's particular drop out.


def get_reload_info(TState):
    """The 'reload' must know where to go in case that the reload succeeds 
       and in case that it fails:
       
       -- If the reload succeeds it must reenter the same state. If the 
          entries are not uniform, the entry must be identified by 'state key'. 
          
       -- If the reload fails the current state's drop out section must be 
          entered. The routing to state's particular drop out section happens
          from the templates central drop out at the end of the transition map.
    """
    if TState.uniform_entries_f:
        ok_state_str = None # Default: Template's common entry
    else:
        ok_state_str = "template_%i_map_state_key_to_entry_index[template_state_key]" \
                       % TState.index

    # DropOut is handled at the end of the transition map.
    # From there, it is routed by the state_key to the particular drop out.
    fail_state_str = "QUEX_LABEL(%i)" % get_address("$drop-out", TState.index, U=True, R=True)

    return ok_state_str, fail_state_str

