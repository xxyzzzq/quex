# (C) 2009 Frank-Rene Schaefer
import os
import sys
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.utf8_state_split      as utf8_state_split
import quex.engine.state_machine.utf16_state_split     as utf16_state_split
import quex.engine.state_machine.nfa_to_dfa            as nfa_to_dfa
import quex.engine.state_machine.hopcroft_minimization as hopcroft
from   quex.engine.misc.file_in                        import error_msg
from   quex.blackboard                                 import setup as Setup

sys.path.append(os.environ["QUEX_PATH"])

def DELETED_do(X, TrafoInfo=None, FH=-1, LineN=None):
    """The side info contains information about line number and
       character number which has to be determined before the 
       pre- and post- contexts are stuck to the state machine.

       When we do a transformation the side information may get
       lost, since we create a new state machine. Since we cannot
       dissolve easily post contexts, we preserve the side info
       and stick it to the result after the operation.
    """
    side_info        = X.side_info
    result           = _do(X, TrafoInfo, FH, LineN)
    result.side_info = side_info

    return result

def DELETED__do(X, TrafoInfo, FH, LineN):
    """Transforms a given state machine from 'Unicode Driven' to another
       character encoding type.
    
       RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!

       X = state machine or number set
    """
    assert X.__class__.__name__ in ["StateMachine", "NumberSet"]
    if X.__class__.__name__ == "StateMachine": 
        assert X.is_DFA_compliant()

    if TrafoInfo is None:
        TrafoInfo = Setup.buffer_codec_transformation_info
        if TrafoInfo is None: return X

    assert TrafoInfo is not None
    if X.__class__.__name__ == "NumberSet": return do_set(X, TrafoInfo, FH, LineN)

    if isinstance(TrafoInfo, (str, unicode)):
        if   TrafoInfo == "utf8-state-split":  return __split(X, utf8_state_split)
        elif TrafoInfo == "utf16-state-split": return __split(X, utf16_state_split)
        # Other transformations are not supported
        assert False
    
    # Pre-condition SM is transformed inside the member function
    X.transform(TrafoInfo)

    sm = __get_DFA_compliant_version(X)
    if sm is not None: 
        X = sm
    sm = __get_DFA_compliant_version(X.core().pre_context_sm())
    if sm is not None: 
        X.replace_pre_context_state_machine(sm)
    sm = __get_DFA_compliant_version(X.core().post_context_backward_input_position_detector_sm())
    if sm is not None: 
        X.replace_post_context_backward_input_position_detector_state_machine(sm)

def try_this(X, FH=None):
    """Transforms a given state machine from 'Unicode Driven' to another
       character encoding type.
    
       RETURNS: Transformed state machine. It may be the same as it was 
                before if there was no transformation actually.
    """
    if X is None: return X

    assert isinstance(X, StateMachine)
    assert X.is_DFA_compliant()

    TrafoInfo = Setup.buffer_codec_transformation_info
    if TrafoInfo is None: return X

    if isinstance(TrafoInfo, (str, unicode)):
        if   TrafoInfo == "utf8-state-split":  return __DFA(utf8_state_split.do(X))
        elif TrafoInfo == "utf16-state-split": return __DFA(utf16_state_split.do(X))
        else:                                  assert False
    
    # Pre-condition SM is transformed inside the member function
    X.transform(TrafoInfo)
    return __DFA(X)

def __DFA(SM):
    if   SM is None:            return None
    elif SM.is_DFA_compliant(): return SM

    result = nfa_to_dfa.do(SM)
    result = hopcroft.do(result, CreateNewStateMachineF=False)
    return result

def __DELETED_get_DFA_compliant_version(SM):
    if   SM is None:            return None
    elif SM.is_DFA_compliant(): return None

    result = nfa_to_dfa.do(SM)
    result = hopcroft.do(result, CreateNewStateMachineF=False)
    return result
        
def __DELETED_split(sm, splitter_module):
    """sm              -- the state machine of which the state shall be split.
       splitter_module -- the mode with the 'do' function that 
                          performs the state split.
    """
    # (*) Core State Machine
    result = splitter_module.do(sm)
    repaired_result = __get_DFA_compliant_version(result)
    if repaired_result is not None: result = repaired_result

    # (*) Pre-Context State Machine
    sm = sm.core().pre_context_sm()
    if sm is not None: 
        new_sm = splitter_module.do(sm)
        repaired_sm = __get_DFA_compliant_version(new_pre_sm)
        if repaired_sm is not None: new_sm = repaired_sm
        result.replace_pre_context_state_machine(new_sm)

    # (*) Pseudo-Ambiguous Post Context
    sm = sm.core().post_context_backward_input_position_detector_sm()
    if sm is not None: 
        new_sm = splitter_module.do(sm)
        repaired_sm = __get_DFA_compliant_version(new_pre_sm)
        if repaired_sm is not None: new_sm = repaired_sm
        result.replace_post_context_backward_input_position_detector_state_machine(new_sm)

    return result

def do_set(number_set, TrafoInfo, FH=-1):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo is not None
    assert TrafoInfo.__class__.__name__ == "NumberSet"

    if type(TrafoInfo) == str:
        if TrafoInfo == "utf8-state-split": 
            result = utf8_state_split.do_set(number_set)
            if result is None:
                error_msg("Operation 'number set transformation' failed 'utf8'.\n" + \
                          "The given number set results in a state sequence not a single transition.", FH, LineN) 
            return result
        # Other transformations are not supported
        assert False
    
    return number_set.transform(TrafoInfo)
        

