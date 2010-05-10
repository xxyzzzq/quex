"""
    key_list_for_state = [ StateIdx0, StateIdx1, ...]

    QUEX_GOTO_STATE(key_list_for_state[0])

    switch( Key ) {
         case 0:  goto StateIdx;
         case 1:  goto Y;
         case 3:
    }

"""
import quex.core_engine.generator.state_coder.core       as state_coder
import quex.core_engine.generator.state_coder.transition as transition
import quex.core_engine.state_machine.index              as index
import quex.core_engine.state_machine.core               as state_machine

class TemplateTarget:
    def __init__(self, TemplateIndex, TargetStateKey):
        """TemplateIndex     = integer that identifies the template.

           TemplatedStateKey = key of the state that is templated inside
                               the template. This parameter is defined before
                               entrance into the template.

           TemplateIndex and TemplatedStateKey identify the array of target
           indices of which the actual target state is to be chosen.

           TargetStateKey    = key of the target state. This allows to select
                               the target state to which to go.
        """
        self.template_index      = TemplateIndex
        self.target_state_index  = TargetStateKey

class TemplateState(state_machine.State):
    def __init__(self, Combi):
        self.__involved_state_list  = Combi.involved_state_list()

        # The template gets an index as if it was a normal state
        self.state_index = index.get()

        # Internally, we adapt the trigger map from:  Interval -> Target State List
        # to:                                         Interval -> Index
        # where 'Index' represents the Target State List
        self.trigger_map          = []
        self.target_state_list_db = []
        i = 0
        for info in Combi.get_trigger_map():
            if type(info[1]) != list:
                # Target state is the same for all involved states
                target = info[1]
            else:
                if info[1] not in self.target_state_list_db: 
                    # Register a new target state combination
                    self.target_state_list_db.append(info[1])
                    target_state_index = i
                    i += 1

                else:
                    # Target state combination has been registered before => get the index.
                    target_state_index = self.target_state_list_db.index(info[1])

                target = TemplateTarget(self.state_index, target_state_index)

            self.trigger_map.append([info[0], target])

    def involved_state_list(self):
        return self.__involved_state_list

    def get_target_state_list(self, StateIndex):
        # Get the 'key' for the state index
        try:    key_index = self.__involved_state_list.index(StateIndex)
        except: assert False, \
                "Required state index not included in template.\n" + \
                "StateIndex %i not in involved state list.\n" % StateIndex + \
                "Involved states are " + repr(self.__involved_state_list)[1:-1]

        result = []
        for target_state_list in self.target_state_list_db:
            if type(target_state_list) != list: continue
            result.append(target_state_list[key_index])

        return result
       
def do(CombinationList, DSM):
    """-- Returns generated code for all templates.
       -- Sets the template_compression_db in DSM.
    """
    assert type(CombinationList) == list
    assert DSM.__class__.__name__ == "StateMachineDecorator"

    # -- get code for the 'key' definitions
    key_definition = []
    # -- get code for each combination
    code = []
    # -- combine all indices of states involved in templates
    state_index_list = []
    # -- database that maps: state index --> template index, state_key
    template_db = {}
    for combination in CombinationList:
        the_template = TemplateState(combination)

        code.append(state_coder.do(the_template, the_template.state_index, DSM, InitStateF=False)
        
        key_definition.extend(__generate_key_definition(the_template))

        state_key = 0
        for state_index in combination.involved_state_list():
            state_index_list.append(state_index)
            template_db[state_index] = [the_template.state_index, state_key]
            state_key += 1

    DSM.set_template_compression_db(template_db)

    router = __generate_state_index_router(state_index_list, DSM)

    return "".join(key_definition + code + router)

def __generate_key_definition(TheTemplate):
    txt = []
    for represented_state_index in TheTemplate.involved_state_list():
        target_state_index_list = TheTemplate.get_target_state_list(represented_state_index)
        txt.append("QUEX_TYPE_GOTO_LABEL  transition_map_template_%i_state_%i[%i] = {" \
                   % (TheTemplate.state_index, represented_state_index, len(target_state_index_list)))
        for state_index in target_state_index_list:
            txt.append("%i, " % state_index)
        txt.append("};\n")
    return txt

def __generate_state_index_router(StateIndexList, DSM):
    txt = ["switch( target_state_index ) {\n"]
    for state_index in StateIndexList:
        txt.append("case %i: " % state_index)
        txt.append(transition.do(state_index, None, None, DSM))
    txt.append("};\n")
    return txt

