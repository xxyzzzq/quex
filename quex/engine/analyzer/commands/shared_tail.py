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

def find_last_common_command(CL0, CL1, StartI, StartK):
    for i in xrange(StartI,0,-1):
        cmd_i = CL0[i]
        for k in xrange(StartK,0,-1):
            if cmd_i == CL1[k]:
                return i, k
    return None, None

def can_be_moved_to_tail(CL, i):
    """Consider list of commands 'CL' and determine whether the command at 
    position 'i' can be moved to the very last position.
    """
    cmd_i = CL[i]
    for cmd in CL[i+1:]:
        if not commands.is_switchable(cmd_i, cmd): 
            return False
    return True

def get(CL0_orig, CL1_orig):
    """Determines a 'tail of shared commands' between the command lists
    CL0_orig and CL1_orig.
    """
    CL0 = CL0_orig # TODO: Algorithm w/o modifiying CL0/CL1
    CL1 = CL1_orig #       => 'copy' not necessary 
    i = len(CL0) - 1
    k = len(CL1) - 1
    tail = None
    while i >= 0  and k >= 0:
        i, k = find_last_common_command(CL0, CL1, i, k)
        if   i is None:                        break
        elif not can_be_moved_to_tail(CL0, i): break
        elif not can_be_moved_to_tail(CL1, k): break
        if tail is None: tail = [ CL0[i] ]
        else:            tail.append(CL0[i])
        # CL0[i] == CL1[i] has been considered; continue with 'i-1', 'k-1'
        i -= 1
        k -= 1

    return tail

