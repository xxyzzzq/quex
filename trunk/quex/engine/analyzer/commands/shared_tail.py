"""PURPOSE:

This module identifies a 'shared list of commands' in two command lists. A
shared tail is a shared list of commands which can be moved at the end of the
two lists. Example:

       List 1:                         List 2:

            [0] a = *p                      [0] a = *p
            [1] b = a + b                   [1] b = a + b
            [3] c++                         [3] c++       
                                            [4] p++

Here the command 'p++' in list 2 can be moved up just below [0] and the two
lists can be implemented as

       List 1:                         List 2:

            [0] a = *p                      [0] a = *p
             |                              [1] p++
             |                               |
             '------->------.-------<--------'
                            |
                           [0] b = a + b
                           [1] c++       

"""
import quex.engine.analyzer.commands.core as commands
from   copy import copy

def find_last_common(CL0, CL1, StartI, StartK):
    """Finds the last common command in CL0[:StartI], CL1[:StartK].
    That is, it searches for the last command before StartI in CL0
    and before StartK in CL1.
    """
    for i in xrange(StartI,-1,-1):
        cmd_i = CL0[i]
        for k in xrange(StartK,-1,-1):
            if cmd_i == CL1[k]:
                return i, k
    return None, None

def can_be_moved_to_tail(CL, i, ExceptionSet):
    """Consider list of commands 'CL' and determine whether the command at 
    position 'i' can be moved to the very last position.

    The 'ExceptionSet' is the list of indices that do not need to be considered.
    In practical, those are the commands which are supposed to be moved to the
    tail. Thus, the command at 'i' does not have to step over it.
    """
    CmdI = CL[i]
    for k in xrange(i, len(CL)):
        if k in ExceptionSet: 
            continue
        if not commands.is_switchable(CL[k], CmdI): 
            return False
    return True

def get(CL0_orig, CL1_orig):
    """Determines a 'tail of shared commands' between the command lists
    CL0_orig and CL1_orig.
    """
    i = len(CL0) - 1
    k = len(CL1) - 1
    # Set of indices of commands which have been determined to be
    #   -- common and
    #   -- moveable to the tail
    from_0 = set()  # Indices from CL0
    from_1 = set()  # Indices from CL1
    # the tail
    tail   = None
    while i >= 0  and k >= 0:
        i, k = find_last_common(CL0, CL1, i, k)
        if   i is None:                                break
        elif not can_be_moved_to_tail(CL0, i, from_0): break
        elif not can_be_moved_to_tail(CL1, k, from_1): break
        from_0.add(i)
        from_1.add(k)
        if tail is None: tail = [ CL0[i] ]
        else:            tail.append(CL0[i])
        # CL0[i] == CL1[k] has been considered; continue with 'i-1', 'k-1'
        i -= 1
        k -= 1

    tail.reverse()
    return tail

