# special states:
from copy import deepcopy, copy

STATE_TERMINATION = long(-1)     # ID for 'success state'

#     The index is chosen to be globally unique, even though, there is a constraint
#     that all target indices of a state machine must be also start indices. For connecting
#     state machines though, it is much easier to rely on a globaly unique state index.
#
#     NOTE: The index is stored in a 'long' variable. If this variable flows over, then
#           we are likely not be able to implement our state machine due to memory shortage
#           anyway.
__internal_state_index_counter = long(-1)
def get():
    """Returns a unique state index."""
    global __internal_state_index_counter
    __internal_state_index_counter += long(1)
    return __internal_state_index_counter

__map_combination_to_index = {}
def map_state_combination_to_index(combination):
    """Returns index for the given combination. If the given combination
    does **not** have an index, it gets a new one. Else the existing one is
    returned."""
    # if all state machines are in state TERMINATION, then the state needs to be TERMINATION.
    if combination == [ STATE_TERMINATION ] * len(combination): 
        return STATE_TERMINATION

    cc_combination = deepcopy(combination)
    cc_combination.sort()
    key_str = repr(cc_combination)

    if not __map_combination_to_index.has_key(key_str):
        # use state_machine.index.get() to get a new unique index for the combination
        __map_combination_to_index[key_str] = get()  
    
    return __map_combination_to_index[key_str]

__map_state_machine_id_to_state_machine = {}    
__internal_state_machine_id_counter = long(-1)
def register_state_machine(StateMachineRef):
    """Produces a unique id for the state machine. This function is only to be called
       from inside the constructor of class StateMachine."""
    if StateMachineRef in __map_state_machine_id_to_state_machine.values(): 
        raise "error: tried to register state machine twice"
        
    global __internal_state_machine_id_counter
    __internal_state_machine_id_counter += long(1)
    # add the state machine under the give key to the database
    __map_state_machine_id_to_state_machine[__internal_state_machine_id_counter] = StateMachineRef
    return __internal_state_machine_id_counter 
    
def get_state_machine_by_id(StateMachineID):
    if __map_state_machine_id_to_state_machine.has_key(StateMachineID) == False:
        raise "error: state machine '%s' has not been registered." % repr(StateMachineID)
    return __map_state_machine_id_to_state_machine[StateMachineID]    
    
################################################################################    
# Determining the priority of patterns represented as state machines:
# This happens in two steps:
#
#   (1) if there is a relation between two state machines A and B defined in
#       the 'ranking_db' then A is 'superior' to B if:
#    
#               __state_machine_ranking_db[A].has_key(B)    
#
#   (2) A is superior to be if the position is higher, i.e.
#       the 'id' of state machine A is less then the 'id' of
#       state machine B. This is so, because 'less' means that
#       A has been defined before B (id increases each time a 
#       new state machine is defined.    
################################################################################    
__state_machine_ranking_db = {}        
def state_machine_ranking_db_register(SuperiorStateMachineID, InferiorStateMachineID):
    """Logs a relationship between two state machines in an internal database. 
       The information about what state machine is 'superior' to the other is
       important for the decision which pattern (represented by a state machine)
       actually triggered. See function 'get_highest_ranked_state_machine([])'

       The database entry __state_machine_ranking_db[sm_id] contains a list of state
       machines that are 'inferior' to the state machine with id 'sm_id'. 

       NOTE: The non-automatic priviledging is not propperly set up.
             The question is anywhile: will it be useful or do we simply
             line up the patterns and then the priviledges are assigned?
             This solution would imply much less fuss.
    """
    global __state_machine_ranking_db    

    # check if by accident two times the same index was given
    if SuperiorStateMachineID == InferiorStateMachineID:
        raise "state machine of index '%s' cannot be superior to itself" % \
              SuperiorStateMachineID 

    # check if a contradictory relation has been entered before
    if  state_machine_ranking_db_is_superior(InferiorStateMachineID, SuperiorStateMachineID): 
        raise "state machine index '%s' is already superior to '%s'\n" \
              "it was tried to enter '%s' to be superior to '%s'" % \
               (InferiorStateMachineID, SuperiorStateMachineID,
                SuperiorStateMachineID, InferiorStateMachineID)  
    
    def __state_machine_ranking_db_add(key, element):
        if __state_machine_ranking_db.has_key(key): __state_machine_ranking_db[key].append(element)
        else:                                       __state_machine_ranking_db[key] = [ element ]

    __state_machine_ranking_db_add(SuperiorStateMachineID, InferiorStateMachineID)

    # if per definition A < B, thenn all elements between a and B need to be < B.
    # otherwise, one gets into trouble with the sorting algorithm.      
    # if SuperiorStateMachineID - InferiorStateMachineID > 1:
    #   for sm_id in range(InferiorStateMachineID + 1, SuperiorStateMachineID): 
    #      __state_machine_ranking_db_add(sm_id, InferiorStateMachineID)


def state_machine_ranking_db_is_superior(A_id, B_id):
    """Checks for the relation between two state machines recursively. Imagine
       the case where A > X0 (is superior to B), X0 > X1, ... XN > B. In this
       case there is no direct relation between A and B in the database. Thus
       one has to dive through the list of relations. 

       RETURNS: True  if A is superior to B
                False if A is not superior, i.e. either there is no entry
                      that indicates superioty of A over B or B might even
                      be superior to A.
        
       NOTE: The non-automatic priviledging is not propperly set up.
             The question is anywhile: will it be useful or do we simply
             line up the patterns and then the priviledges are assigned?
             This solution would imply much less fuss.

       NOTE: get an impression about the relation of A and B in the ranking db
             call is_superior(A, B) and is_superior(B, A).
    """
    if A_id == B_id: return False
    if __state_machine_ranking_db.has_key(A_id) == False: return False
    
    # first look at the state machine ids that are directly inferior
    directly_inferior_list = __state_machine_ranking_db[A_id]
    # print "##difl:", directly_inferior_list
    if B_id in directly_inferior_list:
        return True 

    # loop over all state machines that are inferior to A
    for inferior_state_machine_id in __state_machine_ranking_db[A_id]:     
        if state_machine_ranking_db_is_superior(inferior_state_machine_id, B_id):
           return True

    # no assumptions made at all           
    return False                                                         

def state_machine_ranking_get_dominating_state_machine(StateMachineID_list):
    """Returns a list of the highest ranked state machines in the given list
       of state machine ids. Note, that the number of 'highest ranked' state machines
       can be more than one, because some state machines might be unrelated according
       to the database '__state_machine_ranking_db'.

       RETURNS: index of dominating state machine

       NOTE: The non-automatic priviledging is not propperly set up.
             The question is anywhile: will it be useful or do we simply
             line up the patterns and then the priviledges are assigned?
             This solution would imply much less fuss.
    """   
    if StateMachineID_list.__class__.__name__ != "list":
        raise "expected list of state machine ids, received '%s'" % repr(StateMachineID_list)
        
    L = len(StateMachineID_list)
    if L == 0:
        raise "empty state machine list received"

    if L < 2: return StateMachineID_list[0]

    # (*) first filter out state machine id that are dominated by db entries
    non_dominated_state_machine_id_list = []
    for sm_id in StateMachineID_list:
        for competitor_id in StateMachineID_list:
            if competitor_id == sm_id: continue
            if state_machine_ranking_db_is_superior(competitor_id, sm_id): 
                # sm_id is dominated: do not add to non-dominated list
                break
        else:
            # no competitor was superior: add to non-dominated list
            non_dominated_state_machine_id_list.append(sm_id)
   
    if non_dominated_state_machine_id_list == []:
        non_dominated_state_machine_id_list = copy(StateMachineID_list)

    # the non-dominated list of state machines is sorted by id value.
    # this corresponds to creation time. an earlier created state machine
    # has precedence over a later created one.
    non_dominated_state_machine_id_list.sort()

    # state machine id that sorts the highest is the 'winner'
    return non_dominated_state_machine_id_list[0] 

def state_machine_ranking_db_sort(StateMachineID_list):
    """Sorts the state machines according to their ranking and their
       registered priority. Sorts the provided list and returns
       also a reference to it.
       
       NOTE: The non-automatic priviledging is not propperly set up.
             The question is anywhile: will it be useful or do we simply
             line up the patterns and then the priviledges are assigned?
             This solution would imply much less fuss.
       
    """    
    def compare_this(A, B):
        if   state_machine_ranking_db_is_superior(A, B): return -1
        elif state_machine_ranking_db_is_superior(B, A): return 1
        else:                                            return cmp(A, B) 

    StateMachineID_list.sort(compare_this)

    return StateMachineID_list
                                                         
