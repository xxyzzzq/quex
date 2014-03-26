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


(C) Frank-Rene Schaefer
"""
import quex.engine.analyzer.commands.core as commands
from   copy import copy

def find_last_common(CL0, CL1, StartI, StartK):
    """Finds the last common command in CL0[:StartI], CL1[:StartK].
    That is, it searches for the last command before StartI in CL0
    and before StartK in CL1. Example:

           i:  0 1 2 3 4 5 6 7 8           k:  0 1 2 3 4 5 6     
              .-.-.-.-.-.-.-.-.-.             .-.-.-.-.-.-.-.
              |g|B|i|j|k|l|A|m|o|             |a|b|c|B|A|e|f|
              '-'-'-'-'-'-'-'-'-'             '-'-'-'-'-'-'-'
                     
    If i=8 and k=6, then the last common command is 'A'. Thus the
    indices of the last common command would be: (6, 4).
    If i=5 and k=6, then the last common command id 'B' and the
    result is (1, 3).
                     
    RETURNS: [0], [1]    Indices of last common command.
             None, None  If no common command is found.
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
    In practical, ExceptionSet contains indices of commands which have been 
    already identified to be moved to the tail. Thus, the command at 'i' will
    not have to step over it. Example

                        .-.-.-.-.-.-.-.-.-.-.-.-.-.-.
                        | | | | | | |A|1|2|3|4|B|C|5|
                        '-'-'-'-'-'-'-'-'-'-'-'-'-'-'

    Imagine 'A' is needs to be moved to the tail, but B and C have already
    been determined to be moved. Since, the command list is supposed to be 
    split like:
                        .-.-.-.-.-.-.-.-.-.-.-.  .-.-.-.
                        | | | | | | |1|2|3|4|5|  |A|B|C|
                        '-'-'-'-'-'-'-'-'-'-'-'  '-'-'-'
                                                  (tail)

    A would only need to step over 1, 2, 3, 4, and 5, but not over B and C.
    Thus B and C would be the ExceptionSet.
    """
    L = len(CL)

    if   i >  L - 1: return False  # There is no command
    elif i == L - 1: return True   # It is already at the tail

    CmdI = CL[i]
    for k in xrange(i+1, L):
        if k in ExceptionSet: 
            continue
        if not commands.is_switchable(CL[k], CmdI): 
            return False
    return True

def get(CL0, CL1):
    """Determines a 'tail of shared commands' between the command lists
    CL0_orig and CL1_orig. Example:

              .-.-.-.-.-.-.-.-.-.             .-.-.-.-.-.-.-.
              |g|C|i|j|B|l|A|m|o|             |C|b|c|B|A|e|f|
              '-'-'-'-'-'-'-'-'-'             '-'-'-'-'-'-'-'

    => Separation into 'heads' and 'tail of shared commands':

                    .-.-.-.-.-.-.             
                    |g|i|j|l|m|o|---.    .-.-.-.     
                    '-'-'-'-'-'-'   +--->|C|B|A|     
                    .-.-.-.-.       |    '-'-'-'   
                    |b|c|e|f|-------'       
                    '-'-'-'-'                   

    The shared commands can be moved to the tail, if the remaining commands
    allow to be overstepped. The advantage of separation is that C, B, A
    needs to be implemented only once.

    RETURNS: [(i, k)] -- A list of tuples with two elements 'i' and 'k'. 
                         Each tuple represents a shared command which is
                         located at position 'i' in CL0 and at position 
                         'k' in CL1.
             None     -- if there are no commands which can be shared 
                         at the tail.
    """
    i = len(CL0) - 1
    k = len(CL1) - 1
    # Set of indices of commands which have been determined to be
    #   -- common and
    #   -- moveable to the tail
    tailees_0 = set()  # Indices from CL0 which can be moved to tail
    tailees_1 = set()  # Indices from CL1 which can be moved to tail
    # the tail
    tail   = None
    while i >= 0  and k >= 0:
        i, k = find_last_common(CL0, CL1, i, k)
        if   i is None:                                   break
        elif not can_be_moved_to_tail(CL0, i, tailees_0): break
        elif not can_be_moved_to_tail(CL1, k, tailees_1): break
        tailees_0.add(i)
        tailees_1.add(k)
        if tail is None: tail = [ (i, k) ]
        else:            tail.append((i, k))
        
        i -= 1  # CL0[i] == CL1[k] has been considered.
        k -= 1  # => continue with 'i-1', 'k-1'

    if tail is None: return None
    tail.reverse()
    return tail

