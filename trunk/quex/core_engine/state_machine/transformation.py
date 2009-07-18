# (C) 2009 Frank-Rene Schaefer
import os
import sys
import codecs
from copy import copy
import quex.core_engine.state_machine.utf8_state_split as utf8_state_split
from   quex.frs_py.file_in import error_msg
from   quex.input.setup import setup as Setup

sys.path.append(os.environ["QUEX_PATH"])

def do(X, TrafoInfo=None, FH=-1, LineN=None):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!

       X = state machine or number set
    """
    assert X.__class__.__name__ in ["StateMachine", "NumberSet"]

    if TrafoInfo == None:
        TrafoInfo = Setup.engine_character_encoding_transformation_info
        if TrafoInfo == None: return X

    assert TrafoInfo != None
    if X.__class__.__name__ == "NumberSet": return do_set(X, TrafoInfo, FH, LineN)

    if type(TrafoInfo) == str:
        if TrafoInfo == "utf8-state-split": 
            pre_sm = X.core().pre_context_sm()
            if pre_sm != None:
                X.core().set_pre_context_sm(utf8_state_split.do(pre_sm))
            return utf8_state_split.do(X)
        # Other transformations are not supported
        assert False
    
    # Pre-condition SM is transformed inside the member function
    return X.transform(TrafoInfo)
        
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
        

