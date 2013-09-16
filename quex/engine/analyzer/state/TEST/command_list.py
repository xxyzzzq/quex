#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.state.entry_action  import *
from   quex.blackboard                          import E_Commands

if "--hwut-info" in sys.argv:
    print "CommandList: get_shared_tail;"
    print "CHOICES:     2-1;"
    sys.exit()

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

count_n = 0
def call(Iterable0, Iterable1):
    global count_n
    cl0      = CommandList.from_iterable(Iterable0)
    cl1      = CommandList.from_iterable(Iterable1)
    result   = CommandList.get_shared_tail(cl0, cl1)
    count_n += 1
    print_cl("This", cl0)
    print_cl("That", cl1)
    print_cl("=> shared_tail:", result)
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
    result = call(L0, L1)
    judge(result, common_cmd, common_is_first_f, other_cmd)

    # (1.1) Add some unrelated commands to list 0
    result = call(L0 + unrelated_cmd_list, L1)
    judge(result, common_cmd, common_is_first_f, other_cmd)

    # (1.2) Add some unrelated commands to list 1
    result = call(L0, L1 + unrelated_cmd_list)
    judge(result, common_cmd, common_is_first_f, other_cmd)

    # (2) Extreme case 1: Both only have the common command
    result = call([common_cmd], [common_cmd])
    assert len(result) == 1
    assert result[0] == common_cmd

    # (3) Extreme case 2: One list is empty 
    #     (inverse case tested by caller's strategy)
    result = call([common_cmd], [])
    assert len(result) == 0                         

def unrelated():
    # (4) Only unrelated commands
    result = call(unrelated_cmd_list, [])
    assert len(result) == 0
    result = call([], unrelated_cmd_list)
    assert len(result) == 0
    result = call(unrelated_cmd_list, unrelated_cmd_list)
    assert result == CommandList.from_iterable(unrelated_cmd_list)

def no_share_but_many():
    def increment(cursor):
        i = 0
        while cursor[i]:
            cursor[i] = False
            i += 1
        if i < len(cursor):
            cursor[i] = True
            return True
        else:
            return False
    cursor  = [ False ] * len(CommandFactory.db)
    id_list = [ cmd_id for cmd_id in CommandFactory.iterkeys() ]

    while increment(cursor):
        id0_list = [ cmd_id for i, cmd_id in enumerate(id_list) if cursor[i] ]
        id1_list = [ cmd_id for i, cmd_id in enumerate(id_list) if not cursor[i] ]
        result = call(id0_list, id1_list)
        assert len(result) == 0

if "2-1" in sys.argv:
    for shared_cmd_id in E_Commands:
        if shared_cmd_id == E_Commands._DEBUG_Commands: continue
        for other_cmd_id in E_Commands:
            if other_cmd_id == E_Commands._DEBUG_Commands: continue
            elif other_cmd_id == shared_cmd_id:            continue

            # print "#______________________________________________________"
            test([shared_cmd_id, other_cmd_id], [shared_cmd_id])
            # print "#_____________________"
            test([other_cmd_id, shared_cmd_id], [shared_cmd_id])

    print "%i tests OK" % count_n
