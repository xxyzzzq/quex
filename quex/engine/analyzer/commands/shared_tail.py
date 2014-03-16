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
        if not is_switchable(cmd_i, cmd): 
            return False
    return True

def is_switchable(A, B):
    """Determines whether the command A and command B can be switched
    in a sequence of commands. This is NOT possible if:
       -- A and B read/write to the same register. 
          Two reads to the same register are no problem.
       -- One of the commands is goto-ing, i.e. branching.
    """
    if commands.is_branching(A.id) or commands.is_branching(B.id): 
        return False

    a_access_iterable = commands.get_register_access_iterable(A)
    b_access_db       = commands.get_register_access_db(B)
    for register_a_id, access_a in a_access_iterable:
        access_b = b_access_db.get(register_a_id)
        if access_b is None:
            # Register from command A is not found in command B
            # => no restriction from this register.
            continue
        elif access_a.write_f or access_b.write_f:
            # Command A or Command B write to the same register.
            # => No switch possible
            return False
        else:
            continue

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

def OLD_get_shared_tail(This, That):
    """DEFINITION 'shared tail':
    
    ! A 'shared tail' is a list of commands. For each command of a        !
    ! shared tail, it holds that:                                         !
    !                                                                     !
    !  -- it appears in 'This' and 'That'.                                !
    !  -- if it is a 'WRITE', there is no related 'READ' or 'WRITE'       !
    !     command in This or That coming after the shared command.        !
    !  -- if it is a 'READ', there no related 'WRITE' command in          !
    !     This or That coming after the shared command.                   !

    The second and third condition is essential, so that the shared tail
    can be implemented from a joining point between 'This' and 'That'.
    Consider

        This:                               That:
        * position = input_p # READ         * position = input_p;
        * ++input_p          # WRITE        * input = *input_p;
        * input = *input_p;                      

    The 'position = input_p' cannot appear after '++input_p'. Let input_p
    be 'x' at the entry of This and That. This and That, both result in
    'position = x'. Then a combination, however, without second and third 
    condition results in

        This:                           That:
        * ++input_p;         # READ     * input = *input_p;
        * input = *input_p;                /
                      \                   /
                       \                 /
                      * position = input_p;   # WRITE (Error for This)

    which in the case of 'This' results in 'position = x + 1' (ERROR).
    """
    def is_related_to_unshared_write(CmdI, CmdList, SharedISet):
        for i in xrange(CmdI+1, len(CmdList)):
            cmd = CmdList[i]
            if CommandFactory.db[cmd.id].write_f and i not in SharedISet: 
                return True
        return False

    def is_related_to_unshared_read_write(CmdI, CmdList, SharedISet):
        for i in xrange(CmdI+1, len(CmdList)):
            cmd = CmdList[i]
            if (CommandFactory.db[cmd.id].write_f or CommandFactory.db[cmd.id].read_f) and i not in SharedISet: 
                return True
        return False

    shared_list = []
    done_k      = set() # The same command cannot be shared twice
    for i, cmd_a in enumerate(This):
        for k, cmd_b in enumerate(That):
            if   k in done_k:    continue
            elif cmd_a != cmd_b: continue
            shared_list.append((cmd_a, i, k))
            done_k.add(k) # Command 'k' has been shared. Prevent sharing twice.
            break         # Command 'i' hass been shared, continue with next 'i'.

    change_f = True
    while change_f:
        change_f     = False
        shared_i_set = set(x[1] for x in shared_list)
        shared_k_set = set(x[2] for x in shared_list)
        i            = len(shared_list) - 1
        while i >= 0:
            candidate, this_i, that_k = shared_list[i]
            if     CommandFactory.db[candidate.id].write_f \
               and (   is_related_to_unshared_read_write(this_i, This, shared_i_set) \
                    or is_related_to_unshared_read_write(that_k, That, shared_k_set)):
                del shared_list[i]
                change_f = True
            if     CommandFactory.db[candidate.id].read_f \
               and (   is_related_to_unshared_write(this_i, This, shared_i_set) \
                    or is_related_to_unshared_write(that_k, That, shared_k_set)):
                del shared_list[i]
                change_f = True
            else:
                pass
            i -= 1
            print "#i", i
        print "#change_f", change_f

    return CommandList.from_iterable(cmd for cmd, i, k in shared_list) 

