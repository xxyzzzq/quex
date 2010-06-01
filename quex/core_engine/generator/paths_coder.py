"""Path Compression ___________________________________________________________

   Consider the file 'core_engine/state_machine/compression/paths.py' for 
   a detailed explanation of path compression.

   Code Generation ____________________________________________________________

   Let 'path walker' be a code fragment that is able to 'walk' along a given
   path and follow a 'skeleton', i.e. a general transition map, if the current
   character is not the one of the path. As described in the above file, 
   a state is defined by a 'path walker' index and an iterator position that
   points to the position of a specific character string. Following code
   fragments need to be generated:

   (1) The pathes, i.e. array containing identified sequences, e.g.

        QUEX_CHARACTER_TYPE   path_0 = { 'o', 'r' }; 
        QUEX_CHARACTER_TYPE   path_1 = { 'h', 'i', 'l', 'e' }; 
        QUEX_CHARACTER_TYPE   path_2 = { 'e', 't', 'u', 'r', 'n' }; 

       The init state shall usually not be a path state. It rather routes
       to paths. This is why identified pathes usually do not contain the
       first character of a related keyword. Note, however, that quex 
       may find paths that are not explicitly considered by the user.

   (2) The path walker.

       The path walker consist of a 'prolog' where the current input character
       is checked whether it belongs to the path, and the remainging trigger
       map, in case that the path is left, e.g.

         PATH_WALKER_1:
            /* Single Character Check */
            if   input == *path_iterator: ++path_iterator; goto PATH_WALKER_1
            elif *path_iterator == 0:     goto STATE_3

            /* Common Transition Map */
            if   x < 'a': drop out
            elif x > 'z': drop out
            else:         goto STATE_4

   (3) State entries

       When pathes are keywords, then states that belong to a path are not
       entered except through 'path walk' along the character sequence.
       Theoretically, however, a state of a path might be entered from
       everywhere. Thus, at least for those states that are entered from
       somewhere, a path entry must be provided. 

       A path entry consists of: setting the path iterator and goto the
       related path walker. Additionally, state attributes, such as 
       'acceptance' and 'store_input_position' must be considered. 
       Example:

          STATE_10:
                path_iterator = path_0;
                goto PATH_WALKER_1;
          STATE_11:
                path_iterator = path_0 + 1;
                goto PATH_WALKER_1;
          ...
            
    (4) State router, this might be necessary, if states are non-uniform.
        Because, after reload the current state entry must passed by again.
        In buffer based analyzis no state router is required. Example of 
        a state router (same as for template compression):
        
        
            switch( state_index ) {
            case 2222: goto STATE_2222;
            case 3333: goto STATE_3333;
            ...
            }
"""
from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

import quex.core_engine.generator.state_coder.core             as state_coder
import quex.core_engine.generator.state_coder.transition       as transition
import quex.core_engine.generator.state_coder.input_block      as input_block
import quex.core_engine.generator.state_coder.acceptance_info  as acceptance_info
import quex.core_engine.generator.state_coder.transition_block as transition_block
import quex.core_engine.generator.state_coder.drop_out         as drop_out
import quex.core_engine.state_machine.index                    as index
import quex.core_engine.state_machine.core                     as state_machine

import quex.core_engine.state_machine.compression.paths as paths 


from copy import deepcopy
from quex.input.setup import setup as Setup


LanguageDB = None # Set during call to 'do()', not earlier

def do(SMD):
    """RETURNS: Array 'x'

       x[0] transition target definitions in terms of a 
            local variable database
       x[1] code for templates and state entries
       x[2] state router for template targets
       x[3] involved_state_index_list
    """
    assert isinstance(SMD, StateMachineDecorator)
          
    # (1) Find possible state combinations
    path_list = paths.do(SMD.sm())

    # (2) Implement code for template combinations
    path_array_definitions,   \
    code,                     \
    router,                   \
    involved_state_index_list =  _do(path_list, SMD)

    local_variable_db = path_array_definitions
    if len(local_variable_db) != 0:
        local_variable_db.update({
          "path_iterator"   [ "QUEX_TYPE_GOTO_LABEL", "(QUEX_TYPE_GOTO_LABEL)0x0"],
          "path_state_key": [ "int",                  "(int)0"],
        })

    return "".join(code + router), \
           local_variable_db, \
           involved_state_index_list

def _do(PathList, SMD):
    """-- Returns generated code for all templates.
       -- Sets the template_compression_db in SMD.
    """
    global LanguageDB 

    assert type(PathList) == list
    assert isinstance(SMD, StateMachineDecorator)

    LanguageDB = Setup.language_db
    state_db   = SMD.sm().states

    # -- Collect all indices of states involved in templates
    involved_state_index_list   = set([])

    variable_db = {}
    # -- hold a list that contains also a 'path_id' for each path
    path_list = []

    # (1) The pathes, i.e. array containing identified sequences, e.g.
    for path in PathList:
        assert isinstance(path, paths.CharacterPath)

        path_id = index.get()
        __add_path_definition(variable_db, path, path_id) 
        path_list.append((path, path_id))

    # (2) The path walker.
    code = []
    for path, path_id in path_list:
        __path_walker(path, path_id)


        # Two Scenarios for settings at state entry (last_acceptance_position, ...)
        # 
        #   (i) All state entries are uniform: 
        #       -- Then, a representive state entry can be implemented at the 
        #          template entry. 
        #       -- Recursion happens to the template entry.
        #
        #   (ii) One or more state entry are different (non-uniform):
        #       -- The particularities of each state entry need to be implemented
        #          at state entry.
        #       -- Recursion is routed to entries of involved states.
        #      
        involved_state_list = combination.involved_state_list()
        if SMD.sm().init_state_index in involved_state_list:
            # It is conceivable, that even the init state is part of 
            # a template. In this case, the template **must** be non-uniform.
            # The unit state requires a special entry.
            prototype = None
        else:
            prototype           = state_db.get(involved_state_list[0])
            prev_state          = prototype
            for state_index in involved_state_list[1:]:
                state = state_db.get(state_index)
                assert state != None
                if    prev_state.core().is_equivalent(state.core())       == False \
                   or prev_state.origins().is_equivalent(state.origins()) == False:
                    prototype = None
                    break

        # -- create template state for combination object
        #    prototype == None, tells that there state entries differ and there
        #                       is no representive state.
        template = TemplateState(combination, SMD.sm().get_id(), index.get(), 
                                 prototype)
        template_list.append(template)

        # -- collect indices of involved states
        involved_state_index_list.update(involved_state_list)

        # -- collect indices of target states
        for state_index in template.transitions().get_target_state_index_list():
            if state_index != None: 
                target_state_index_list.add(state_index)
            else:
                # 'goto drop-out' is coded in state index list as 'minus template index'
                target_state_index_list.add(- template.core().state_index)

        # -- if the template is non-uniform, then we need a router that maps to
        #    each state entry of involved states (e.g. for recursion and after reload).
        if not template.uniform_state_entries_f():
            target_state_index_list.update(involved_state_list)

    # -- transition target definition for each templated state
    transition_target_definition = {}
    for template in template_list:
        __transition_target_data_structures(transition_target_definition, template)

    # -- template state entries
    # -- template state
    code = []
    for template in template_list:
        __templated_state_entries(code, template, SMD)
        __template_state(code, template, SMD)

    # -- state router
    if len(template_list) != 0:
        router = __state_router(target_state_index_list, SMD)
    else:
        router = []

    return transition_target_definition, code, router, involved_state_index_list

class TemplateTarget:
    def __init__(self, TemplateIndex, TargetIndex=None, UniformStateEntriesF=False):
        """TemplateIndex identifies the template that 'hosts' the transition.

           TargetIndex identifies the target number (Target0, Target1, ... in
                       the example on the top of this file).

           The transition code generator will later on generate code of the 
           form 
           
                       goto Template$X$_Target$Y$[state_key];

           Where '$X$' is replaced with TemplateIndex and $Y$ is replaced
           with TargetIndex.
        """
        self.template_index = TemplateIndex
        self.target_index   = TargetIndex
        self.__uniform_state_entries_f = UniformStateEntriesF

    def recursive(self):
        return self.target_index == None

    def uniform_state_entries_f(self):
        """If the state entries are not uniform, then recursion must
           jump to state entries, rather the template entry.
        """
        return self.__uniform_state_entries_f

class TransitionMapMimiker:
    """Class that mimiks the TransitionMap of module

                   quex.core_engine.state_machine.transition_map 
                   
       The goal is to enable 'TemplateState' to act as a normal state
       responding to the member function .transitions().
    """
    def __init__(self, TemplateIndex, TriggerMap, UniformStateEntriesF):
        self.__trigger_map          = []
        self.__target_state_list_db = []
        i = 0
        for interval, target in TriggerMap:

            if target == templates.TARGET_RECURSIVE:
                # Normal Recursion: 
                #   Return to the entry of the template
                # Dedicated Recursion: 
                #   This holds if one or more involved states require things to be set
                #   at state entry (e.g. last_acceptance = ..). Then, the recursion 
                #   needs to happen to the state entries.
                target = TemplateTarget(TemplateIndex,  
                                        TargetIndex          = None, # says recursion!
                                        UniformStateEntriesF = UniformStateEntriesF) 

            elif type(target) == list:
                if target not in self.__target_state_list_db: 
                    # Register a new target state combination
                    self.__target_state_list_db.append(target)
                    target_index = i
                    i += 1

                else:
                    # Target state combination has been registered before => get the index.
                    target_index = self.__target_state_list_db.index(target)

                target = TemplateTarget(TemplateIndex, target_index)

            self.__trigger_map.append([interval, target])

    def get_trigger_map(self):
        return self.__trigger_map

    def get_epsilon_target_state_index_list(self):
        return []

    def get_target_state_index_list(self):
        """Return list of all target states that are possibly entered from 
           the templated states.
        """
        result = set([])
        for target_state_list in self.__target_state_list_db:
            result.update(target_state_list)
        return result

    def get_map(self):
        """We need to return something that is not empty, so that the reload
           procedure will be implemented. See module 'state_coder.acceptance_info'.
        """
        return { -1: None }

    def target_state_list_db(self):
        return self.__target_state_list_db

class TemplateState(state_machine.State):
    """Implementation of a Template that is able to play the role of a
       state machine state. It is constructed on the basis of a 
       TemplateCombination object that is create by module
       
                state_machine.compression.templates

       Goal of this definition is to have a state that is able to 
       comply the requirements of 'state_coder.core'. Thus, the
       template can be generated through the same procedure as 
       all state machine states.
    """
    def __init__(self, Combi, StateMachineID, StateIndex, RepresentiveState):
        """Combi contains all information about the states of a template
                 and the template itself.
           
           StateIndex is the state index that is assigned to the template.

           RepresentiveState is a state that can represent all states in
                             the template. All states of a template must
                             be equivalent, so any of them can do.

                             If == None, then it means that state entries
                             differ and there is no representive state.
        """
        assert isinstance(Combi, templates.TemplateCombination)
        assert isinstance(RepresentiveState, state_machine.State) or RepresentiveState == None
        assert type(StateIndex) == long

        # (0) Components required to be a 'State'
        if RepresentiveState != None:
            self.__uniform_state_entries_f = True
            core        = deepcopy(RepresentiveState.core())
            origin_list = deepcopy(RepresentiveState.origins())
        else:
            self.__uniform_state_entries_f = False
            # Empty core and origins, since the particularities are handled at individual 
            # state entries.
            core        = state_machine.StateCoreInfo(StateMachineID, StateIndex, 
                                                      AcceptanceF=False)   
            origin_list = state_machine.StateOriginList()          

        state_machine.State._set(self, core, origin_list,
                # Internally, we adapt the trigger map from:  Interval -> Target State List
                # to:                                         Interval -> Index
                # where 'Index' represents the Target State List
                TransitionMapMimiker(StateIndex, Combi.get_trigger_map(), 
                                     self.__uniform_state_entries_f))

        state_machine.State.core(self).state_index = StateIndex

        # (1) Template related information
        self.__template_combination    = Combi

    def uniform_state_entries_f(self):
        return self.__uniform_state_entries_f

    def template_combination(self):
        return self.__template_combination

def __add_path_definition(variable_db, Path, PathID):
    """Defines the transition targets for each involved state.
    """
    txt = []
    for character in Path.sequence():
        txt.append("%i," % character)
    txt.append("0x0")

    variable_name  = "path_%i" % PathID
    variable_type  = "QUEX_TYPE_CHARACTER"
    dimension      = len(Path.sequence() + 1)
    variable_value = "{ " + "".join(txt) + "}"

    variable_db[variable_name] = [ variable_type, variable_value, dimension ]

def __templated_state_entries(txt, TheTemplate, SMD):
    """Defines the entries of templated states, so that the state key
       for the template is set, before the jump into the template. E.g.

            STATE_4711: 
               key = 0; goto TEMPLATE_STATE_111;
            STATE_3123: 
               key = 1; goto TEMPLATE_STATE_111;
            STATE_8912: 
               key = 2; goto TEMPLATE_STATE_111;
    """
    for key, state_index in enumerate(TheTemplate.template_combination().involved_state_list()):

        # Print the state label
        label_str = LanguageDB["$label-def"]("$entry", state_index)
        if state_index != SMD.sm().init_state_index:
            label_str = "    __quex_assert(false); /* No drop-through between states */\n" + \
                        label_str
        txt.append(label_str)

        state = SMD.sm().states[state_index]
        # If all state entries are uniform, the entry handling happens uniformly at
        # the entrance of the template, not each state.
        if not TheTemplate.uniform_state_entries_f():
            txt.extend(input_block.do(state_index, False, SMD.backward_lexing_f()))
            txt.extend(acceptance_info.do(state, state_index, SMD, ForceSaveLastAcceptanceF=True))
        txt.append("    ")
        txt.append(LanguageDB["$assignment"]("template_state_key", "%i" % key).replace("\n", "\n    "))
        txt.append(LanguageDB["$goto"]("$template", TheTemplate.core().state_index))
        txt.append("\n\n")

def __path_walker(txt, Path, PathID):
    """Generates the path walker, that walks along the character sequence.
    """
    label_str = "    __quex_assert(false); /* No drop-through between states */\n" + \
                LanguageDB["$label-def"]("$path", PathID)
    txt.append(label_str)

    # -- The comparison with the path's current character
    #    If terminating zero is reached, the path's end state is entered.
    txt.append(LanguageDB["$if =="]("*path_iterator"))
    txt.append(LanguageDB["$goto"]("$path", PathID)
    txt.append(LanguageDB["$elseif"] 
               + LanguageDB["$=="]("path_iterator == (QUEX_TYPE_CHARACTER)(0)")
               + LanguageDB["$then"])
    txt.append(LanguageDB["$goto"]("$entry", Path.end_state_index()))

    # -- Transition map of the 'skeleton'        
    trigger_map = Path.skeleton()

    if TheTemplate.uniform_state_entries_f():
        txt.extend(input_block.do(state_index, False, SMD.backward_lexing_f()))
        txt.extend(acceptance_info.do(state, state_index, SMD, ForceSaveLastAcceptanceF=True))
    txt.extend(transition_block.do(TriggerMap, state_index, False, SMD))
    txt.extend(drop_out.do(state, state_index, SMD, False))

def __state_router(StateIndexList, SMD):
    """Create code that allows to jump to a state based on an integer value.
    """

    if SMD.backward_lexing_f(): state_router_label = "STATE_ROUTER_BACKWARD:\n"
    else:                       state_router_label = "STATE_ROUTER:\n"
    txt = [
            state_router_label,
            "    switch( target_state_index ) {\n"
    ]
    for index in StateIndexList:
        txt.append("    case %i: " % index)
        if index >= 0:
            # Transition to state entry
            state_index = index
            code  = transition.do(state_index, None, None, SMD)
        else:
            # Transition to a templates 'drop-out'
            template_index = - index
            code = transition.do(None, template_index, None, SMD)
        txt.append(code)
        txt.append("\n")

    txt.append("    }\n")

    return txt

