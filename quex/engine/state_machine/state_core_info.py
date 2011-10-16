from quex.blackboard import E_PostContextIDs, E_AcceptanceIDs, E_PreContextIDs

# Special Signal Values for 'pre_context_id'
# Add a member '_DEBUG_NAME_Xyz' so that the type of an enum value can
# be determined by value.EnumType[-1]
class StateCoreInfo(object): 
    """-- acceptance_f:

          (if True) When the state is hit, then it 'accepts'. This means that a
          pattern  has matched. 
    
       -- pre_context_id:

          (if True) it says that acceptance is only valid, if the given 
          pre-context is fulfilled.

       -- post_context_id:

          (if not None) When an acceptance state is reached it tells that 
          the input position needs to be restored. This is the counterpart
          to 'store_input_position'. It follows that an acceptance state
          should never store the input position. Otherwise, it would only
          mean that it has to be stored and restored immediately. 

          State machine id of the related post context. This is actually
          nonsense. A post context is connected 1:1 with a state machine
          core pattern. Thus the state machine id is enough. If there is
          not post context, again, the state machine tells enough.

       -- pseudo_ambiguous_post_context_id:
          
          (if not None) it says that upon acceptance the state needs to 
          do a backward input position detection. It was not possible to 
          determine the end of the core pattern of a post context during 
          forward analysis. Where 'post_context_id' indicates that the
          input position was stored in a position register, this variable
          indicates that a backward analysis needs to be performed to
          find the end of the core pattern.

       -- store_input_position_f: 

          (if True) When the state is hit, the position of the input pointer 
          should be stored in a position register. 

          This is used for post contexts. When a core pattern ended, the input
          position needs to be stored and the lexing for the post context
          starts. When the post context reaches acceptance the input position
          is then set to what was stored at the end of the core pattern.

          * Note, this has **nothing** to do with trailing acceptances, where a
          * pattern has matched and a longer pattern is tried to matched.
          * Example 'for' has matched, we have 'fores' and try to match 'forest'.
          * If there is not 't' following 'forest', we should go back to the
          * end of 'for'. Those effects are handled with the 'last acceptance
          * position' and it is determined during track analysis.

    """    
    __slots__ = ("state_machine_id", "state_index", 
                 "__acceptance_f", 
                 "__store_input_position_f",
                 "__post_context_id", 
                 "__pre_context_id", 
                 "__pre_context_begin_of_line_f",
                 "__pseudo_ambiguous_post_context_id")

    def __init__(self, StateMachineID, StateIndex, AcceptanceF, StoreInputPositionF=False, 
                 PostContextID=E_PostContextIDs.NONE, 
                 PreContext_StateMachineID=E_PreContextIDs.NONE,
                 PreContext_BeginOfLineF=False,
                 PseudoAmbiguousPostConditionID=-1L):
        assert PreContext_StateMachineID != -1L # Catch the old definitions (this is superfluous after some time)
        assert type(StateIndex) == long
        assert type(AcceptanceF) == bool
        assert type(StoreInputPositionF) == bool
        assert    StateMachineID in E_AcceptanceIDs \
               or (isinstance(StateMachineID, long) and StateMachineID >= 0) 
        assert PostContextID in E_PostContextIDs or PostContextID >= 0
        assert PreContext_StateMachineID in E_PreContextIDs or isinstance(PreContext_StateMachineID, long)

        if PreContext_BeginOfLineF: 
            assert PreContext_StateMachineID in [E_PreContextIDs.BEGIN_OF_LINE, E_PreContextIDs.NONE]

        if AcceptanceF: 
            assert not StoreInputPositionF 
        else:
            assert PreContext_StateMachineID      == E_PreContextIDs.NONE
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
        self.__post_context_id = PostContextID

        # -- was the origin a pre-conditioned acceptance?
        #    (then one has to check at the end if the pre-condition holds)
        if PreContext_BeginOfLineF: 
            self.__pre_context_id = E_PreContextIDs.BEGIN_OF_LINE
        else:
            self.__pre_context_id = PreContext_StateMachineID  

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
                             self.pre_context_begin_of_line_f(),
                             self.__pseudo_ambiguous_post_context_id)

    def is_equivalent(self, Other):
        if self.__acceptance_f != Other.__acceptance_f:         return False
        elif self.__acceptance_f:
            if self.state_machine_id != Other.state_machine_id: return False

        return     self.store_input_position_f()           == Other.store_input_position_f()           \
               and self.__post_context_id                  == Other.__post_context_id                  \
               and self.__pre_context_id                   == Other.__pre_context_id                   \
               and self.pre_context_begin_of_line_f()      == Other.pre_context_begin_of_line_f()    \
               and self.__pseudo_ambiguous_post_context_id == Other.__pseudo_ambiguous_post_context_id 

    def merge(self, Other):
        # It **DOES** make any sense to merge to state cores from different
        # state machines. This should NOT be an 'assert'. In the final state machine
        # more than one state machine is combined in parallel and then they belong 
        # to the same state machine
        # if self.state_machine_id != Other.state_machine_id: return

        if Other.__acceptance_f:                 
            self.__acceptance_f           = True
            self.set_store_input_position_f(False)
        elif Other.__store_input_position_f and self.__acceptance_f == False:
            self.set_store_input_position_f(True)

        if Other.__pre_context_id != E_PreContextIDs.NONE:                     self.__pre_context_id  = Other.__pre_context_id 
        if Other.pre_context_begin_of_line_f():               self.__pre_context_id = E_PreContextIDs.BEGIN_OF_LINE 

        if Other.__post_context_id != E_PostContextIDs.NONE:  self.__post_context_id = Other.__post_context_id

        if Other.__pseudo_ambiguous_post_context_id != -1L: 
            self.__pseudo_ambiguous_post_context_id = Other.__pseudo_ambiguous_post_context_id

    def is_unconditional_acceptance(self):
        return     self.__acceptance_f \
               and self.__pre_context_id == E_PreContextIDs.NONE

    def is_acceptance(self):
        return self.__acceptance_f

    def set_acceptance_f(self, Value, LeaveStoreInputPositionF):
        """NOTE: By default, when a state is set to acceptance the input
                 position is to be stored for all related origins, if this is 
                 not desired (as by 'post_context_append.do(..)' the flag
                 'store_input_position_f' is to be adapted manually using the
                 function 'set_store_input_position_f'
        """      
        assert type(Value) == bool
        self.__acceptance_f = Value
        # default: store_input_position_f follows acceptance_f
        ## STEP: if not LeaveStoreInputPositionF: self.set_store_input_position_f(Value)
        
    def set_store_input_position_f(self, Value=True):
        assert type(Value) == bool
        if Value == True: assert self.__acceptance_f == False
        self.__store_input_position_f = Value

    def set_pre_context_id(self, Value=True):
        assert Value != -1L # Catch the old definitions (this is superfluous after some time)
        assert Value in E_PreContextIDs or type(Value) == long
        self.__pre_context_id = Value

    def set_pre_context_begin_of_line_f(self, Value=True):
        assert type(Value) == bool
        if Value == True:
            self.__pre_context_id = E_PreContextIDs.BEGIN_OF_LINE
        else:
            self.__pre_context_id = E_PreContextIDs.NONE

    def set_post_context_id(self, Value):
        assert   (isinstance(Value, long) and Value >= 0) \
               or Value in E_PostContextIDs
        self.__post_context_id = Value

    def set_post_context_backward_detector_sm_id(self, Value):
        assert type(Value) == long
        self.__pseudo_ambiguous_post_context_id = Value

    def pre_context_id(self):
        return self.__pre_context_id  

    def post_context_id(self):
        return self.__post_context_id     

    def pre_context_begin_of_line_f(self):
        return self.__pre_context_id == E_PreContextIDs.BEGIN_OF_LINE

    def store_input_position_f(self):
        if self.__acceptance_f: return False
        return self.__store_input_position_f    

    def pseudo_ambiguous_post_context_id(self):
        return self.__pseudo_ambiguous_post_context_id

    def is_end_of_post_contexted_core_pattern(self):
        return self.post_context_id() != E_PostContextIDs.NONE and self.store_input_position_f()
                            
    def __cmp__(self, Other):
        if self.is_acceptance() == True  and Other.is_acceptance() == False: return -1
        if self.is_acceptance() == False and Other.is_acceptance() == True:  return 1

        # NOTE: The state machine ID directly corresponds to the 'position in the list'
        #       where the pattern was specified. Low ID == early specification.
        return cmp(self.state_machine_id, Other.state_machine_id)
            
    def __eq__(self, other):
        """Two origins are the same if they origin from the same state machine and 
           have the same state index. If they then differ in the 'store_input_position_f'
           there is a major error. It would mean that one StateOriginInfo states about the
           same original state something different than another StateOriginInfo.
        """
        result = self.state_machine_id == other.state_machine_id and \
                 self.state_index      == other.state_index                           

        if result == True: 
            assert self.__store_input_position_f == other.__store_input_position_f, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the input being stored or not.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)
            assert self.__pre_context_id == other.__pre_context_id, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the pre-conditioned acceptance.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)
            assert self.__post_context_id == other.__post_context_id, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the post-conditioned acceptance.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)

        return result     

    def __repr__(self):
        return self.get_string()

    def get_string(self, StateMachineAndStateInfoF=True):
        txt = ""

        if 1: 
            # ONLY FOR TEST: state.core
            if False and not StateMachineAndStateInfoF:
                if self.__acceptance_f: return "*"
                else:                   return ""

            if StateMachineAndStateInfoF:
                if self.state_machine_id != E_AcceptanceIDs.FAILURE:
                    txt += ", " + repr(self.state_machine_id).replace("L", "")
                if self.state_index != -1L:
                    txt += ", " + repr(self.state_index).replace("L", "")
            if self.__acceptance_f:        
                txt += ", A"
                if self.__post_context_id != E_PostContextIDs.NONE:  
                    txt += ", R" + repr(self.__post_context_id).replace("L", "")
            else:
                if self.__store_input_position_f:        
                    assert self.__post_context_id != E_PostContextIDs.NONE
                    txt += ", S" + repr(self.__post_context_id).replace("L", "")

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
        else:
            open("/tmp/horror.txt", "wb").write("terribel\n")
            import sys
            sys.exit(-1)

