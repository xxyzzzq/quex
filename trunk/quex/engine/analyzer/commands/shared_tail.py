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

from   itertools import islice
from   copy import copy

def find_last_common(CL0, DoneSet0, CL1, DoneSet1):
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
    for i, cmd_i in reversed([(p, cmd) for p, cmd in enumerate(CL0) if p not in DoneSet0]):
        for k, cmd_k in reversed([(q, cmd) for q, cmd in enumerate(CL1) if q not in DoneSet1]):
            if cmd_i == cmd_k: 
                return i, k
    return None, None

def can_be_moved_to_tail(CL, i, L, DoneSet):
    """Consider list of commands 'CL' and determine whether the command at 
    position 'i' can be moved to the very last position.

    The 'DoneSet' is the list of indices that do not need to be considered.
    In practical, DoneSet contains indices of commands which have been 
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
    Thus B and C would be the DoneSet.
    """
    if   i >  L - 1: return False  # There is no command
    elif i == L - 1: return True   # It is already at the tail

    cmd_i = CL[i]
    for k in xrange(i+1, L):
        if k in DoneSet:                          continue
        elif not commands.is_switchable(CL[k], cmd_i): return False
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

    RETURNS: 
        
    [0] The list of commands which can be shared as a tuple.
        None, else.
    [1] The list of indices of 'tail commands' CL0. Those are to be 
        cut from CL0, if the commands shall really be move to the 
        tail.
    [2] List of indices of 'tail commands' in CL1.
    """
    Li = len(CL0)
    i  = Li - 1
    Lk = len(CL1)
    k  = Lk - 1
    # Set of indices of commands which have been determined to be
    #   -- common and
    #   -- moveable to the tail
    i_moved_to_tail = set()  # Indices from CL0 which can be moved to tail
    k_moved_to_tail = set()  # Indices from CL1 which can be moved to tail
    while i >= 0  and k >= 0:
        i, k = find_last_common(CL0, i_moved_to_tail, CL1, k_moved_to_tail)
        if   i is None:                                             break
        elif not can_be_moved_to_tail(CL0, i, Li, i_moved_to_tail): break
        elif not can_be_moved_to_tail(CL1, k, Lk, k_moved_to_tail): break
        i_moved_to_tail.add(i)
        k_moved_to_tail.add(k)

    if len(i_moved_to_tail) == 0: 
        return None, None, None
    else:
        i_cut_list = sorted(list(i_moved_to_tail)) # 'small' first
        tail = tuple(CL0[i] for i in i_cut_list)   # 'small' first
        i_cut_list.sort(reverse=True)                            # 'great' first
        k_cut_list = sorted(list(k_moved_to_tail), reverse=True) # 'great' first
        return tail, i_cut_list, k_cut_list

