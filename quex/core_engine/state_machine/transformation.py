# (C) 2009 Frank-Rene Schaefer
import os
import sys
import codecs
from copy import copy
sys.path.append(os.environ["QUEX_PATH"])

import quex.input.codec_db as codec_db
import quex.core_engine.utf8 as utf8
from   quex.core_engine.interval_handling import NumberSet, Interval
import quex.core_engine.state_machine as state_machine
from   quex.core_engine.state_machine.core import State

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
        

