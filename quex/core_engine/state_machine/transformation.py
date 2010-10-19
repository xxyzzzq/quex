# (C) 2009 Frank-Rene Schaefer
import os
import sys
import codecs
from copy import copy
import quex.core_engine.state_machine.utf8_state_split  as utf8_state_split
import quex.core_engine.state_machine.utf16_state_split as utf16_state_split
from   quex.frs_py.file_in                              import error_msg
from   quex.input.setup                                 import setup as Setup

sys.path.append(os.environ["QUEX_PATH"])

def do(X, TrafoInfo=None, FH=-1, LineN=None):
    """Transforms a given state machine from 'Unicode Driven' to another
       character encoding type.
    
       RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!

       X = state machine or number set
    """
    assert X.__class__.__name__ in ["StateMachine", "NumberSet"]
    if X.__class__.__name__ == "StateMachine": 
        assert X.is_DFA_compliant()

    if TrafoInfo == None:
        TrafoInfo = Setup.engine_character_encoding_transformation_info
        if TrafoInfo == None: return X

    assert TrafoInfo != None
    if X.__class__.__name__ == "NumberSet": return do_set(X, TrafoInfo, FH, LineN)

    if type(TrafoInfo) == str:
        if TrafoInfo == "utf8-state-split": 
            return __split(X, utf8_state_split)

        elif TrafoInfo == "utf16-state-split":
            return __split(X, utf16_state_split)

        # Other transformations are not supported
        assert False
    
    # Pre-condition SM is transformed inside the member function
    X.transform(TrafoInfo)

    # After transformation NFA to DFA and Hopcroft optimization must be performed
    result = X
    if not result.is_DFA_compliant(): result = nfa_to_dfa.do(result)
    result = hopcroft.do(result, CreateNewStateMachineF=False)

    pre_sm = result.core().pre_context_sm()
    if pre_sm != None:
        if not X.is_DFA_compliant(): pre_sm = nfa_to_dfa.do(pre_sm)
        pre_sm = hopcroft.do(pre_sm, CreateNewStateMachineF=False)
        result.replace_pre_context_state_machine(pre_sm)
    return result

        
def __split(sm, splitter_module):
    """sm              -- the state machine of which the state shall be split.
       splitter_module -- the mode with the 'do' function that 
                          performs the state split.
    """
    result = splitter_module.do(sm)
    pre_sm = sm.core().pre_context_sm()
    if pre_sm == None: return result

    # There is a pre-context, state machine needs to be adapted
    new_pre_sm = splitter_module.do(pre_sm)
    result.replace_pre_context_state_machine(new_pre_sm)

    return result

def do_set(number_set, TrafoInfo, FH=-1, LineN=None):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo != None
    assert TrafoInfo.__class__.__name__ == "NumberSet"

    if type(TrafoInfo) == str:
        if TrafoInfo == "utf8-state-split": 
            result = utf8_state_split.do_set(number_set)
            if result == None:
                error_msg("Operation 'number set transformation' failed 'utf8'.\n" + \
                          "The given number set results in a state sequence not a single transition.", FH, LineN) 
            return result
        # Other transformations are not supported
        assert False
    
    return number_set.transform(TrafoInfo)
        

