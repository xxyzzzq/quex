# (C) 2009-2011 Frank-Rene Schaefer
import quex.engine.generator.state.transition.core  as transition_block
from   quex.engine.generator.state.transition.code  import TextTransitionCode
import quex.engine.generator.state.drop_out         as drop_out_coder
import quex.engine.generator.state.entry            as entry_coder
from   quex.engine.generator.state.core             import input_do
from   quex.engine.generator.languages.address      import get_address, get_label
from   quex.engine.generator.languages.variable_db  import variable_db

import quex.engine.analyzer.template.core           as templates 
from   quex.engine.analyzer.state_entry_action      import SetStateKey, TransitionID, DoorID

from   quex.blackboard import setup as Setup, E_StateIndices, E_Compression
from   itertools       import ifilter
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

def do(txt, TState, TheAnalyzer):
    """Generate code for given template state 'TState'. This follows the 
       scheme of code generation for AnalyzerState-s in 'state_coder/core.py'.
    """
    global LanguageDB
    LanguageDB = Setup.language_db
    variable_db.require("state_key")

    # (*) Request necessary variable definition _______________________________
    #     (BEFORE we translate the transition map, somehow)
    __require_data(TState, TheAnalyzer)

    # (*) Entry _______________________________________________________________
    entry_coder.do(txt, TState, TheAnalyzer) 

    # (*) Access input character ______________________________________________
    input_do(txt, TState) 

    # (*) Transition Map ______________________________________________________
    prepare_transition_map(TState)
    transition_block.do(txt, 
                        TState.transition_map, 
                        TState.index, 
                        TState.engine_type, 
                        TState.init_state_f, 
                        TheAnalyzer   = TheAnalyzer, 
                        DebugStateStr = "    __quex_debug_template_state(%i, state_key);\n" % TState.index)

    # (*) Drop Out ____________________________________________________________
    __drop_out(txt, TState, TheAnalyzer)

    return 

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
    #     (The rules for having or not having a label here are complicated, 
    #      so rely on the label's usage database.)
    txt.append("%s:\n" % get_label("$drop-out", TState.index))
    txt.append("   __quex_debug_template_drop_out(%i, state_key);\n" % TState.index)

    # (*) Drop Out Section(s)
    if TState.uniform_drop_outs_f:
        # -- uniform drop outs => no switch required
        prototype = TheAnalyzer.state_db[TState.state_index_list[0]]
        tmp = []
        drop_out_coder.do(tmp, prototype, TheAnalyzer, DefineLabelF=False)
        txt.extend(tmp)
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

    case_txt = LanguageDB.SELECTION("state_key", case_list)
    LanguageDB.INDENT(case_txt)
    txt.extend(case_txt)

def __require_data(TState, TheAnalyzer):
    """Defines the transition targets for each involved state.
    """
    def help(AdrList):
        return "".join(["{ "] + map(lambda adr: "QUEX_LABEL(%i), " % adr, AdrList) + [" }"])

    for target_scheme in sorted(TState.target_scheme_list, key=attrgetter("index")):
        assert len(target_scheme.scheme) == len(TState.state_index_list)
        def address(DoorId):
            if door_id == E_StateIndices.DROP_OUT:
                return get_address("$drop-out", TState.index, U=True, R=True)
            else:
                return LanguageDB.ADDRESS_BY_DOOR_ID(door_id)

        address_list = [ address(door_id) for door_id in target_scheme.scheme ]

        variable_db.require_array("template_%i_target_%i", 
                                  ElementN = len(TState.state_index_list), 
                                  Initial  = help(address_list),
                                  Index    = (TState.index, target_scheme.index))

    # Recursion can only occur, if all entries enter the state via the 'empty door', 
    # i.e. where there is no action to be done. Thus, RECURSIVE can be translated
    # to 'Door 0' of the template state.
    if not TState.entries_empty_f:
        def recursion_address(StateIndex):
            """On recursion, the state key does not have to be set a second time. 
               If the door where the state enters itself does nothing else, but
               setting the state key, one can enter via the parent's door.
            """
            door_id = TState.entry.door_db[TransitionID(StateIndex, StateIndex)]
            door    = TState.entry.door_find(door_id)
            assert door is not None
            if door.parent is not None:
                # If the door has no other command, then setting the state key, 
                # then the parent can take its role: For recursion the state key
                # does not have to be set again.
                for found in (x for x in door.common_command_list if not isinstance(x, SetStateKey)):
                    break # There is a command, other than 'SetStateKey'
                else:
                    return LanguageDB.ADDRESS_BY_DOOR_ID(door.parent.door_id)

            return LanguageDB.ADDRESS_BY_DOOR_ID(door_id)

        for found in (x for x in TState.transition_map if x[1].recursive_f): 
            # HERE:     Non-uniform entries 
            #       and there is at least one recursive entry
            address_list = [ recursion_address(i) for i in TState.state_index_list ]
            variable_db.require_array("template_%i_map_state_key_to_recursive_entry", 
                                      ElementN = len(TState.state_index_list), 
                                      Initial  = help(address_list),
                                      Index    = TState.index)
            # Once, we have cleared this up, there is no need to consider any further example.
            break

    # Drop outs: all drop outs end up at the end of the transition map, where
    # it is routed via the state_key to the state's particular drop out.

def handle_source_state_dependent_transitions(transition_map, TheAnalyzer, 
                                              StateKeyStr, StateIndexList):
    """Templates and Pathwalkers may trigger in their transition map to states
       where the entry depends on the source state. Such transition maps may 
       operate on behalf of different states. The state is identified by a
       state key.
    """
    return
    LanguageDB = Setup.language_db

    for i, info in enumerate(transition_map):
        interval, target_index = info
        if not isinstance(target_index, (int, long)): continue

        entry = TheAnalyzer.state_db[target_index].entry
        if entry.uniform_doors_f(): continue

        # (*) Code: Transition to Specific State Entry based on current state.
        case_list = []
        # A common target state of a template is targeted by all involved states.
        # => If the target state's entries depend on the source state all
        #    states in the template's state_index_list must be mentioned as entry.
        for state_key, from_state_index in enumerate(StateIndexList):
            if not entry.has_special_door_from_state(from_state_index): from_state_index = None
            case_list.append((state_key, LanguageDB.GOTO(target_index, from_state_index))) 

        code = LanguageDB.SELECTION(StateKeyStr, case_list)
        LanguageDB.INDENT(code, 2)
        target = TextTransitionCode(["\n"] + code)

        transition_map[i] = (interval, target)

def prepare_transition_map(TheState):
    """Generates code for transition map of a template state.

       NOTE: A word about the reload procedure.
       
       Reload can end either with success (new data has been loaded), or failure
       (no more data available). In case of success the **only** the transition
       step has to be repeated. Nothing else is effected.  Stored positions are
       adapted automatically.
       
       By convention we redo the transition map, in case of reload success and 
       jump to the state's drop-out in case of failure. There is no difference
       here in the template state example.
    """
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

        elif target.recursive_f:
            # The state key does not have to be set again. So, if the entry door
            # of the recursion does nothing more than setting a state key, we 
            # can directly go to its parent. This, though is coded already in 
            #
            # 'template_%i_map_state_key_to_recursive_entry[state_key]'. 
            #  
            # EXCEPTION: If no state requires any action (except the 'SetStateKey'), 
            #            then we can go directly to the 'Door 0', the door where 
            #            nothing is to be done. No aforementioned array is required.
            if TheState.entries_empty_f:
                text = LanguageDB.GOTO_BY_DOOR_ID(DoorID(XStateIndex, DoorIndex=0))
            else:
                get_label("$state-router", U=True) # Ensure reference of state router
                label = "template_%i_map_state_key_to_recursive_entry[state_key]" % TheState.index
                text  = LanguageDB.GOTO_BY_VARIABLE(label)

        elif target.door_id is not None:
            text = LanguageDB.GOTO_BY_DOOR_ID(target.door_id)

        else:
            get_label("$state-router", U=True) # Ensure reference of state router
            # Transition target depends on state key
            label = "template_%i_target_%i[state_key]" % (TheState.index, target.index)
            text  = LanguageDB.GOTO_BY_VARIABLE(label)

        # Replace target 'i' by written text
        target            = TextTransitionCode([text])
        transition_map[i] = (interval, target)

