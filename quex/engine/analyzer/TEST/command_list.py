#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.commands import *
from   quex.blackboard               import E_Cmd
import quex.engine.analyzer.command_list_shared_tail as command_list_shared_tail

from   collections import defaultdict
from   copy import deepcopy

if "--hwut-info" in sys.argv:
    print "CommandList: get_shared_tail;"
    print "CHOICES:     2-1, no-common, all-common, misc;"
    sys.exit()

sys.exit() # The whole test must be written again!

def print_cl(name, CL):
    print "#%s:" % name
    print "    " + str(CL).replace("\n", "\n    ")

def is_read(Cmd):
    return CommandFactory.db[Cmd.id].read_f

def is_write(Cmd):
    return CommandFactory.db[Cmd.id].write_f

def get_cmd(CmdId):
    content_type = CommandFactory.db[CmdId].content_type
    if   content_type is None:            args = None
    elif issubclass(content_type, tuple): args = tuple([ 0 ] * len(content_type._fields))
    else:                                 args = None

    return CommandFactory.do(CmdId, args)

def judge(Result, CommonCmd, CommonIsFirstF, OtherCmd):
    # General asserts:
    assert len(Result) <= 1
    if len(Result) == 1: assert Result[0] == CommonCmd, "%s" % str(CommonCmd)

    # Detailed rules:
    if not CommonIsFirstF: 
        # If the common command is second (i.e. last)
        # => it MUST appear in the common tail.
        assert len(Result) == 1
        assert Result[0] == CommonCmd
    else:
        if is_write(CommonCmd):
            # If common command is first and 'write', then it can
            # only be shared if 'other' is not 'read' or 'write'.
            if is_write(OtherCmd) or is_read(OtherCmd):
                assert len(Result) == 0
            else:
                assert len(Result) == 1
                assert Result[0] == CommonCmd

        elif is_read(CommonCmd):
            # If common command is first and 'read', then it can
            # only be shared if 'other' is not 'write'.
            if is_write(OtherCmd):
                assert len(Result) == 0
            else:
                assert len(Result) == 1
                assert Result[0] == CommonCmd
        else:
            # Commands which are irrelevant to 'read' or 'write'
            # must always be shared.
            assert len(Result) == 1
            assert Result[0] == CommonCmd

count_db = defaultdict(int)
def call(Name, Iterable0, Iterable1):
    global count_db
    cl0      = CommandList.from_iterable(Iterable0)
    cl1      = CommandList.from_iterable(Iterable1)
    # print "#cl0:", cl0
    # print "#cl1:", cl1
    result   = command_list_shared_tail.get(cl0, cl1)
    count_db[Name] += 1
    # print_cl("This", cl0)
    # print_cl("That", cl1)
    # print_cl("=> shared_tail:", result)
    return result

def test(IdList0, IdList1):

    L0  = [ get_cmd(cmd_id) for cmd_id in IdList0 ]
    L1  = [ get_cmd(cmd_id) for cmd_id in IdList1 ]
    # The potentially common command is the one from the list 
    # with one command.
    if len(L0) == 1: 
        assert len(L1) == 2
        common_cmd = L0[0]
        if L1[0] == common_cmd: other_cmd = L1[1]; common_is_first_f = True
        else:                   other_cmd = L1[0]; common_is_first_f = False
    elif len(L1) == 1: 
        assert len(L0) == 2
        common_cmd = L1[0]
        if L0[0] == common_cmd: other_cmd = L0[1]; common_is_first_f = True
        else:                   other_cmd = L0[0]; common_is_first_f = False
    else:              
        assert False

    unrelated_cmd_list = [ 
        get_cmd(cmd_id)
        for cmd_id, info in CommandFactory.db.iteritems()
            if not info.read_f and not info.write_f and cmd_id != common_cmd.id and cmd_id != other_cmd.id
    ]

    # (1) The pure case
    result = call("normal", L0, L1)
    judge(result, common_cmd, common_is_first_f, other_cmd)

    # (1.1) Add some unrelated commands to list 0
    result = call("normal + unrelated", L0 + unrelated_cmd_list, L1)
    judge(result, common_cmd, common_is_first_f, other_cmd)

    # (1.2) Add some unrelated commands to list 1
    result = call("normal + unrelated", L0, L1 + unrelated_cmd_list)
    judge(result, common_cmd, common_is_first_f, other_cmd)

class Cursor:
    """Iterates over the combinations: command in one list, but not in the other.
    """
    def __init__(self):
        self.flags       = [ False ] * len(CommandFactory.db)
        self.cmd_id_list = [ cmd_id for cmd_id in CommandFactory.db.iterkeys() ]

    def step(self):
        i = 0
        print "#flags:", self.flags
        while i < len(self.flags) and self.flags[i]:
            self.flags[i] = False
            i += 1
        if i < len(self.flags):
            self.flags[i] = True
            return True
        else:
            return False

    def get_lists(self):
        list0 = [ get_cmd(cmd_id) for i, cmd_id in enumerate(self.cmd_id_list) if self.flags[i] ]
        list1 = [ get_cmd(cmd_id) for i, cmd_id in enumerate(self.cmd_id_list) if not self.flags[i] ]
        return list0, list1

if "2-1" in sys.argv:
    for shared_cmd_id in E_Cmd:
        if shared_cmd_id == E_Cmd._DEBUG_Commands: continue
        for other_cmd_id in E_Cmd:
            if other_cmd_id == E_Cmd._DEBUG_Commands: continue
            elif other_cmd_id == shared_cmd_id:            continue

            # print "#______________________________________________________"
            test([shared_cmd_id, other_cmd_id], [shared_cmd_id])
            # print "#_____________________"
            test([other_cmd_id, shared_cmd_id], [shared_cmd_id])

elif "no-common" in sys.argv:
    cursor = Cursor()
    while cursor.step():
        cmd0_list, cmd1_list = cursor.get_lists()
        result = call("[%i][%i]" % (len(cmd0_list), len(cmd1_list)), cmd0_list, cmd1_list)
        assert len(result) == 0

elif "all-common" in sys.argv:
    cursor = Cursor()
    while cursor.step():
        cmd_list, dummy = cursor.get_lists()
        result = call("[%i][%i]" % (len(cmd_list), len(cmd_list)), cmd_list, deepcopy(cmd_list))
        assert len(result) == len(cmd_list)

elif "misc" in sys.argv:
    for cmd_id in E_Cmd:
        if cmd_id == E_Cmd._DEBUG_Commands: continue
        cmd = get_cmd(cmd_id)
        result = call("only one common", [cmd], [cmd])
        assert len(result) == 1
        assert result[0] == cmd

        for other_cmd_id in E_Cmd:
            if   other_cmd_id == E_Cmd._DEBUG_Commands: continue
            elif other_cmd_id == cmd_id: continue
            other_cmd = get_cmd(other_cmd_id)
            result = call("1-1 no common", [cmd], [other_cmd])
            assert len(result) == 0

        result = call("one command, one list empty", [cmd], [])
        assert len(result) == 0                         
        result = call("one command, one list empty", [], [cmd])
        assert len(result) == 0                         

#elif "block" in sys.argv:
#    write_cmd  = None
#    write_cmd2 = None
#    read_cmd   = None
#    read_cmd2  = None
#    for cmd_id, info in CommandFactory.db.iteritems():
#        if info.write_f:
#            if   write_cmd  is None: write_cmd  = get_cmd(cmd_id) 
#            elif write_cmd2 is None: write_cmd2 = get_cmd(cmd_id) 
#        if info.read_f:
#            if   read_cmd  is None: read_cmd  = get_cmd(cmd_id) 
#            elif read_cmd2 is None: read_cmd2 = get_cmd(cmd_id) 
#
#    cl0 = CommandList.from_iterable([write_cmd, read_cmd])
#    cl0 = CommandList.from_iterable([write_cmd, read_cmd])



L = max(len(x) for x in count_db.keys())
for name, count in sorted(count_db.iteritems()):
    print "%s:%s %i x OK" % (name, " " * (L - len(name)), count)

