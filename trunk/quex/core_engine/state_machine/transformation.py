import os
import sys
sys.path.append(os.environ["QUEX_PATH"])

import quex.input.codec_db as codec_db

def do(sm, TrafoInfo, FH=-1, LineN=None):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo != None
    
    return sm.transform(TrafoInfo)
        

def do_set(number_set, TrafoInfo, FH=-1, LineN=None):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo != None
    
    return number_set.transform(TrafoInfo)
        





