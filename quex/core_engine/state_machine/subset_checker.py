class Checker:
    def __init__(self, SuperSM, AllegedSubSM):
        """Checks wether all patterns matched by the SuperSM are also matched by the 
           AllegedSubSM. Basically it tries to answer the question:

              ? Is the set of patterns matched by 'AllegedSubSM' a subset of the ?
              ? set of patterns matched by 'SuperSM'                              ?

           RETURNS: 'True'  if so,
                    'False' if not.
        """
        self.sub   = AllegedSubSM
        self.super = SuperSM
        self.visited_state_index_db = {}

    def do(self):
        return self.__dive(self.sub.init_state_index, [self.super.init_state_index])

    def __dive(self, SubSM_StateIndex, SuperSM_StateIndexList):
        """SubSM_StateIndex:       refers to a state in the alleged subset state machine.

           SuperSM_StateIndexList: list of states in the 'super set' state machine that
                                   was reached by the same trigger set as SubSM_StateIndex.      
                                   They are the set of states that can 'mimik' the current
                                   state indexed by 'SubSM_StateIndex'.
        """
        # (*) Determine the states behind the indices
        sub_state        = self.sub.states[SubSM_StateIndex]
        super_state_list = map(lambda index: self.super.states[index], SuperSM_StateIndexList)
        #     Bookkeeping
        self.visited_state_index_db[SubSM_StateIndex] = True
        #     Union of all triggers were the 'mimiking' super states trigger.
        #     (For speed considerations, keep it in prepared, so it does not have to 
        #      be computed each time it is required.)
        super_trigger_set_union_db = {} 
        for index in SuperSM_StateIndexList:
            super_trigger_set_union_db[index] = self.super.states[index].transitions().get_trigger_set_union()

        # (*) Here comes the condition:
        #
        #     For every trigger (event) in the 'sub sm state' that triggers to a follow-up state
        #     there must be pendant triggering from the mimiking 'super sm states'.
        #
        #     If a trigger set triggers to an 'acceptance' state, then all mimiking 'super sm states' 
        #     must trigger to an 'acceptance' state. Thus, saying that the 'super sm' also recognizes
        #     the pattern that was reached until here can be matched by the 'super set sm'. If not
        #     all mimiking state machines would trigger on the trigger set to an acceptance state,
        #     this means that there is a path to an acceptance state in 'subset sm' that the 'super
        #     sm' has no correspondance. Thus, then the claim to be a super set state machine can
        #     be denied.
        #
        for target_index, trigger_set in sub_state.transitions().get_map().items():
            target_state = self.sub.states[target_index]

            # (*) Require that all mimiking states in the 'super sm' trigger to a valid
            #     target state on all triggers in the trigger set. 
            #     
            #     This is true, if the union of all trigger sets of a mimiking 'super state'
            #     covers the trigger set. It's not true, if not. Thus, use set subtraction:
            for index in SuperSM_StateIndexList:
                if trigger_set.difference(super_trigger_set_union_db[index]).is_empty() == False:
                    return False

            # (*) Collect the states in the 'super set sm' that can be reached via the 'trigger_set'
            super_target_state_index_list = []
            for super_state in super_state_list:
                for index in super_state.transitions().get_resulting_target_state_index_list(trigger_set):
                    if index in super_target_state_index_list: continue
                    super_target_state_index_list.append(index)

            # (*) The acceptance condition: 
            if target_state.is_acceptance():
                # (*) Require that all target states in 'super sm' reached by 'trigger_set' are 
                #     acceptance states, otherwise the alleged 'sub sm' has found a pattern which
                #     is matched by it and which is not matched by 'super sm'. Thus, the claim 
                #     that the alleged 'sub sm' is a sub set state machine can be repudiated.
                for index in super_target_state_index_list:
                    if self.super.states[index].is_acceptance() == False: return False

            # (*) No need to go along loops, do not follow paths to states already visited.
            if not self.visited_state_index_db.has_key(target_index):
                if self.__dive(target_index, super_target_state_index_list) == False: return False

        # If the condition held for all sub-pathes of all trigger_sets then we can reports
        # that the currently investigated sub-path supports the claim that 'sub sm' is a
        # sub set state machine of 'super sm'.
        return True

def do(SuperSM, AllegedSubSM):
    return Checker(SuperSM, AllegedSubSM).do()
