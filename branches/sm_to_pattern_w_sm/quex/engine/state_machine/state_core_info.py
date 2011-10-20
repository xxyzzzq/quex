from quex.blackboard import E_PostContextIDs, E_AcceptanceIDs, E_PreContextIDs

# Special Signal Values for 'pre_context_id'
# Add a member '_DEBUG_NAME_Xyz' so that the type of an enum value can
# be determined by value.EnumType[-1]
class StateCoreInfo(object): 
    """A StateCoreInfo tells about a state how it should behave in a state
       machine that represents one single isolated pattern. This is in 
       contrast to a state machine that consists of a conglomerate of 
       patterns combined into a single machine.

       Such a state of an isolated pattern needs has the following
       actions related to attributes:

       -- acceptance_f:

          (if True) When the state is hit, then it 'accepts'. This means that a
          pattern  has matched. 
    
       -- pre_context_id:

          (if True) it says that acceptance is only valid, if the given 
          pre-context is fulfilled.

       Pre contexts are checked by a backward analysis before the actual forward
       analysis. In the frame of this backward analysis matched pre-contexts raise
       a flag as soon as a pre-context is fulfilled. Those flags are checked if the 
       'pre_context_id' is not NONE.

       Post contexts are appended to the pattern. For example 'hello/world' is
       a pattern that matches 'hello' if it is followed by 'world'. This is
       implemented by a single concatenated state machine that matches
       'helloworld'. When acceptance is reached, though, it goes back to where
       'hello' ended its match. Consequently, there are states were the input
       position has to be stored, and others where the input position has to be
       restored. Of course, the restoring of input positions makes only sense
       in acceptance states. The storing of input positions, then makes only 
       sense in non-acceptance states. Otherwise, storing and restoring would 
       happen in the same state and therefore be superfluous.

       -- store_store_input_position_f:

          When the state is hit, the input position has to be stored. 
          Such a state can never be an acceptance state. 
          
       -- restore_input_position_f:

          When the state is hit the input position has to be restored. 
          Such a state **must** be an acceptance state.

       Some post contexts cannot be addressed by simple storing and restoring
       of input positions. They require a backward search. Such cases are 
       indicated by the following flag:
          
       -- pseudo_ambiguous_post_context_id:
          
          (if not None) it says that upon acceptance the state needs to 
          do a backward input position detection. When the acceptance of
          this pattern is determined a backward search engine needs to be
          started that searches for the correct input position for the
          next run.
      _________________________________________________________________________

      NOTE: Again, objects of this type describe the behavior of a state 
            in a single isolated state machine, designed to match one single
            pattern. 

            The exact behavior of a state in a 'melted' state machine is
            derived from lists of these objects by track analysis.
    """    
    __slots__ = ("state_machine_id", "state_index", 
                 "__acceptance_f", 
                 "__pre_context_id", 
                 "__store_input_position_f",
                 "__restore_input_position_f",
                 "__post_context_id", 
                 "__pseudo_ambiguous_post_context_id")

    def __init__(self, StateMachineID, StateIndex, 
                 AcceptanceF, 
                 StoreInputPositionF=False, 
                 PostContextID=E_PostContextIDs.NONE, 
                 PreContextID=E_PreContextIDs.NONE,
                 PseudoAmbiguousPostConditionID=-1L, 
                 RestoreInputPositionF=False):
        assert type(StateIndex)  == long
        assert type(AcceptanceF) == bool
        assert type(StoreInputPositionF) == bool
        assert type(RestoreInputPositionF) == bool
        assert    StateMachineID in E_AcceptanceIDs \
               or (isinstance(StateMachineID, long) and StateMachineID >= 0) 
        assert PostContextID in E_PostContextIDs or PostContextID >= 0
        assert PreContextID  in E_PreContextIDs or isinstance(PreContextID, long)

        if AcceptanceF: 
            assert not StoreInputPositionF 
        else:
            assert PreContextID                   == E_PreContextIDs.NONE
            assert PseudoAmbiguousPostConditionID == -1L
               
        # NOT: StateMachineID != E_AcceptanceIDs.FAILURE => AcceptanceF == False
        #      State core info objects are also used for non-acceptance states of patterns

        self.state_machine_id = StateMachineID
        self.state_index      = StateIndex
        # is an acceptance state?
        self.__acceptance_f   = AcceptanceF 

        # Input position of the current input stream is to be stored in 
        # the following cases: 
        #
        #   -- 'normal acceptance state', i.e. not the acceptance state of a post condition.
        #   -- 'ex acceptance state', i.e. states that were acceptance states of state machines
        #      that have a post condition.      
        #
        # NOTE: By default, the function 'set_acceptance(True)' and 'set_acceptance(False)'
        #       of class State sets the 'store_input_position_f' to True, respectively
        #       false, because this is the normal case. When a post condition is to be appended
        #       the 'store_input_position_f' is to be stored manually - see the function
        #       'state_machine.post_context_append.do(...).
        self.set_store_input_position_f(StoreInputPositionF)

        # -- was the origin a post-conditioned acceptance?
        #    (then we have to store the input position, store the original state machine
        #     as winner, but continue)
        self.__post_context_id          = PostContextID
        self.__restore_input_position_f = RestoreInputPositionF
        assert self.__restore_input_position_f == (self.__acceptance_f and self.__post_context_id != E_PostContextIDs.NONE)

        # -- was the origin a pre-conditioned acceptance?
        #    (then one has to check at the end if the pre-condition holds)
        self.__pre_context_id = PreContextID  

        # -- id of state machine that is used to go backwards from the end
        #    of a post condition that is pseudo-ambiguous. 
        self.__pseudo_ambiguous_post_context_id = PseudoAmbiguousPostConditionID

    def clone(self, StateIndex=None):
        if StateIndex is not None: state_index = StateIndex
        else:                      state_index = self.state_index
        return StateCoreInfo(self.state_machine_id, state_index, 
                             self.__acceptance_f,
                             self.__store_input_position_f,
                             self.__post_context_id,
                             self.__pre_context_id,
                             self.__pseudo_ambiguous_post_context_id, 
                             self.__restore_input_position_f)

    def is_equivalent(self, Other):
        if self.__acceptance_f != Other.__acceptance_f:         return False
        elif self.__acceptance_f:
            if self.state_machine_id != Other.state_machine_id: return False
        return     self.store_input_position_f()           == Other.store_input_position_f()           \
               and self.restore_input_position_f()         == Other.restore_input_position_f()         \
               and self.__pre_context_id                   == Other.__pre_context_id                   \
               and self.__pseudo_ambiguous_post_context_id == Other.__pseudo_ambiguous_post_context_id 

    def merge(self, Other):
        # It **DOES** make any sense to merge to state cores from different
        # state machines. This should NOT be an 'assert'. In the final state machine
        # more than one state machine is combined in parallel and then they belong 
        # to the same state machine
        # if self.state_machine_id != Other.state_machine_id: return

        if Other.__acceptance_f:                 
            self.__acceptance_f = True
            self.set_store_input_position_f(False)
        elif Other.__store_input_position_f and self.__acceptance_f == False:
            self.set_store_input_position_f(True)

        if Other.__pre_context_id != E_PreContextIDs.NONE:    self.__pre_context_id  = Other.__pre_context_id 
        if Other.__post_context_id != E_PostContextIDs.NONE:  self.__post_context_id = Other.__post_context_id

        self.__restore_input_position_f = (self.__acceptance_f and self.__post_context_id != E_PostContextIDs.NONE)

        if Other.__pseudo_ambiguous_post_context_id != -1L: 
            self.__pseudo_ambiguous_post_context_id = Other.__pseudo_ambiguous_post_context_id

    def is_unconditional_acceptance(self):
        return     self.__acceptance_f \
               and self.__pre_context_id == E_PreContextIDs.NONE

    def is_acceptance(self):
        return self.__acceptance_f

    def set_acceptance_f(self, Value):
        """NOTE: By default, when a state is set to acceptance the input
                 position is to be stored for all related origins, if this is 
                 not desired (as by 'post_context_append.do(..)' the flag
                 'store_input_position_f' is to be adapted manually using the
                 function 'set_store_input_position_f'
        """      
        assert type(Value) == bool
        self.__acceptance_f = Value
        self.__restore_input_position_f = (self.__acceptance_f and self.__post_context_id != E_PostContextIDs.NONE)

    def set_post_context_id(self, Value):
        assert   (isinstance(Value, long) and Value >= 0) or Value in E_PostContextIDs
        # assert isinstance(self.state_machine_id, long) and self.state_machine_id != -1
        self.__post_context_id = Value
        self.__restore_input_position_f = (self.__acceptance_f and self.__post_context_id != E_PostContextIDs.NONE)
        
    def set_store_input_position_f(self, Value=True):
        assert type(Value) == bool
        if Value == True: assert self.__acceptance_f == False
        self.__store_input_position_f = Value

    def restore_input_position_f(self):
        return self.__restore_input_position_f

    def set_pre_context_id(self, Value=True):
        assert Value in E_PreContextIDs or type(Value) == long
        self.__pre_context_id = Value

    def set_post_context_backward_detector_sm_id(self, Value):
        assert type(Value) == long
        self.__pseudo_ambiguous_post_context_id = Value

    def pre_context_id(self):
        return self.__pre_context_id  

    def store_input_position_f(self):
        if self.__store_input_position_f: assert self.__restore_input_position_f == False
        if self.__acceptance_f:           assert self.__store_input_position_f == False
        return self.__store_input_position_f    

    def pseudo_ambiguous_post_context_id(self):
        return self.__pseudo_ambiguous_post_context_id

    def __cmp__(self, Other):
        assert False
            
    def is_same_origin(self, Other):
        """Two origins are the same if they origin from the same state machine and 
           have the same state index. If they then differ in the 'store_input_position_f'
           there is a major error. It would mean that one StateOriginInfo states about the
           same original state something different than another StateOriginInfo.
        """
        result = self.state_machine_id == Other.state_machine_id and \
                 self.state_index      == Other.state_index                           

        if result == True: 
            assert self.__store_input_position_f == Other.__store_input_position_f, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the input being stored or not.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)
            assert self.__pre_context_id == Other.__pre_context_id, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the pre-conditioned acceptance.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)
            assert self.__restore_input_position_f == Other.__restore_input_position_f, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the post-conditioned acceptance.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)

        return result     

    def __repr__(self):
        return self.get_string()

    def get_string(self, StateMachineAndStateInfoF=True):
        txt = ""

        if StateMachineAndStateInfoF:
            if self.state_machine_id != E_AcceptanceIDs.FAILURE:
                txt += ", " + repr(self.state_machine_id).replace("L", "")
            if self.state_index != -1L:
                txt += ", " + repr(self.state_index).replace("L", "")
        if self.__acceptance_f:        
            txt += ", A"
            if self.__restore_input_position_f:
                txt += ", R" 
        else:
            if self.__store_input_position_f:        
                txt += ", S" 

        if self.__pre_context_id != E_PreContextIDs.NONE:            
            if self.__pre_context_id == E_PreContextIDs.BEGIN_OF_LINE:
                txt += ", pre=bol"
            else: 
                txt += ", pre=" + repr(self.__pre_context_id).replace("L", "")

        if self.__pseudo_ambiguous_post_context_id != -1L:            
            txt += ", papc=" + repr(self.__pseudo_ambiguous_post_context_id).replace("L", "")

        # Delete the starting ", "
        if len(txt) > 2: txt = txt[2:]

        return "(%s)" % txt

