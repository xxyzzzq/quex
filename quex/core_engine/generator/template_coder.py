"""Template Compression _______________________________________________________

   Consider the file 'core_engine/state_machine/compression/templates.py' for 
   a detailed explanation of template compression


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
from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

import quex.core_engine.generator.state_coder.core            as state_coder
import quex.core_engine.generator.state_coder.transition      as transition
import quex.core_engine.generator.state_coder.acceptance_info as acceptance_info
import quex.core_engine.state_machine.index              as index
import quex.core_engine.state_machine.core               as state_machine

import quex.core_engine.state_machine.compression.templates as templates 


from copy import deepcopy
from quex.input.setup import setup as Setup


LanguageDB = None # Set during call to 'do()', not earlier

def do(DSM, CostCoefficient):
    """RETURNS: Array 'x'

       x[0] transition target definitions 
       x[1] code for templates and state entries
       x[2] state router for template targets
       x[3] involved_state_index_list
    """
    assert isinstance(DSM, StateMachineDecorator)
          
    # (1) Find possible state combinations
    combination_list = templates.do(DSM.sm(), CostCoefficient)

    # (2) Implement code for template combinations
    transition_target_definition, \
    code,                         \
    router,                       \
    involved_state_index_list     =  _do(combination_list, DSM)

    prolog = transition_target_definition \
             + ["QUEX_TYPE_GOTO_LABEL target_state_index;\n", \
                "int                  template_state_key;\n"]

    return "".join(code + router), "".join(prolog), \
           involved_state_index_list

def _do(CombinationList, DSM):
    """-- Returns generated code for all templates.
       -- Sets the template_compression_db in DSM.
    """
    global LanguageDB 

    assert type(CombinationList) == list
    assert isinstance(DSM, StateMachineDecorator)

    LanguageDB = Setup.language_db

    # -- Collect all indices of states involved in templates
    involved_state_index_list = set([])
    # -- Collect all indices of targets states in the 'adaption table'
    target_state_index_list   = set([])
    # -- Generate 'TemplatedState's for each TemplateCombination
    template_list             = []
    for combination in CombinationList:
        assert isinstance(combination, templates.TemplateCombination)

        # All states of a combination are equivalent, thus it is sufficient 
        # to consider one single state in order to know whether it is
        # acceptance or not.
        prototype_index = combination.involved_state_list()[0]
        prototype       = DSM.sm().states.get(prototype_index)
        assert prototype != None

        # -- create template state for combination object
        template = TemplateState(combination, index.get(), prototype)
        template_list.append(template)

        # -- collect indices of involved states
        involved_state_index_list.update(combination.involved_state_list())

        # -- collect indices of target states
        for state_index in template.transitions().get_target_state_index_list():
            if state_index != None: 
                target_state_index_list.add(state_index)
            else:
                # 'goto drop-out' is coded in state index list as 'minus template index'
                target_state_index_list.add(- template.core().state_index)

    # -- transition target definition for each templated state
    transition_target_definition = []
    for template in template_list:
        __transition_target_data_structures(transition_target_definition, 
                                            template)

    # -- template state entries
    # -- template state
    code = []
    for template in template_list:
        __templated_state_entries(code, template, DSM)
        __template_state(code, template, DSM)

    # -- state router
    router = __state_router(target_state_index_list, DSM)

    return transition_target_definition, code, router, involved_state_index_list

class TemplateTarget:
    def __init__(self, TemplateIndex, TargetIndex=None):
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

    def recursive(self):
        return self.target_index == None

class TransitionMapMimiker:
    """Class that mimiks the TransitionMap of

                   quex.core_engine.state_machine.transition_map 
                   
       The goal is to enable 'TemplateState' to act as a normal state
       responding to the member function .transitions().
    """
    def __init__(self, TemplateIndex, TriggerMap):
        self.__trigger_map          = []
        self.__target_state_list_db = []
        i = 0
        for interval, target in TriggerMap:

            if target == templates.TARGET_RECURSIVE:
                target = TemplateTarget(TemplateIndex) # No target index --> recursion   

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
    def __init__(self, Combi, StateIndex, RepresentiveState):
        """Combi contains all information about the states of a template
                 and the template itself.
           
           StateIndex is the state index that is assigned to the template.

           RepresentiveState is a state that can represent all states in
                             the template. All states of a template must
                             be equivalent, so any of them can do.
        """
        assert isinstance(Combi, templates.TemplateCombination)
        assert isinstance(RepresentiveState, state_machine.State)
        assert type(StateIndex) == long

        # (0) Components required to be a 'State'
        state_machine.State._set(self, 
                deepcopy(RepresentiveState.core()),
                RepresentiveState.origins(),
                # Internally, we adapt the trigger map from:  Interval -> Target State List
                # to:                                         Interval -> Index
                # where 'Index' represents the Target State List
                TransitionMapMimiker(StateIndex, Combi.get_trigger_map()))

        state_machine.State.core(self).state_index = StateIndex

        # (1) Template related information
        self.__template_combination  = Combi

    def template_combination(self):
        return self.__template_combination

def __transition_target_data_structures(txt, TheTemplate):
    """Defines the transition targets for each involved state.
    """
    involved_state_n = len(TheTemplate.template_combination().involved_state_list())
    template_index   = TheTemplate.core().state_index
    for target_index, target_state_index_list in enumerate(TheTemplate.transitions().target_state_list_db()):
        assert len(target_state_index_list) == involved_state_n

        txt.append("QUEX_TYPE_GOTO_LABEL  template_%i_target_%i[%i] = {" \
                   % (template_index, target_index, len(target_state_index_list)))
        for index in target_state_index_list:
            if index != None: txt.append("%i, " % index)
            else:             txt.append("-%i," % template_index)
        txt.append("};\n")

def __templated_state_entries(txt, TheTemplate, DSM):
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
        txt.append(LanguageDB["$label-def"]("$entry", state_index))
        state = DSM.sm().states[state_index]
        txt.extend(acceptance_info.do(state, state_index, DSM, ForceSaveLastAcceptanceF=True))
        txt.append("    ")
        txt.append(LanguageDB["$assignment"]("template_state_key", "%i" % key))
        txt.append("    ")
        txt.append(LanguageDB["$goto"]("$entry", TheTemplate.core().state_index))
        txt.append("\n\n")

def __template_state(txt, TheTemplate, DSM):
    """Generate the template state that 'hosts' the templated states.
    """
    txt.extend(state_coder.do(TheTemplate, TheTemplate.core().state_index, DSM, InitStateF=False))

def __state_router(StateIndexList, DSM):
    """Create code that allows to jump to a state based on an integer value.
    """

    txt = [
            "STATE_ROUTER:\n",
            "    switch( target_state_index ) {\n"
    ]
    for index in StateIndexList:
        txt.append("    case %i: " % index)
        if index >= 0:
            # Transition to state entry
            state_index = index
            code  = transition.do(state_index, None, None, DSM)
        else:
            # Transition to a templates 'drop-out'
            template_index = - index
            code = transition.do(None, template_index, None, DSM)
        txt.append(code)
        txt.append("\n")

    txt.append("    }\n")

    return txt

