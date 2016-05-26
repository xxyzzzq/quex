# TEST: Generation of Loop Map
#
# A 'loop map' associates characters with what has to happen when they occurr.
#
# This test investigates the generation of the state machines only under three
# circumstances expressed as CHOICES:
#
#   Plain:       no parallel state machines.
#   AppendixNoI: a loop with parallel state machines that 
#                do NOT INTERSECT on the first transition.
#   AppendixI:   a loop with parallel state machines that 
#                do INTERSECT.
#   Split:       a state machine's first transition is split
#                into multipl, because it is related to different
#                count actions.
#
# (C) Frank-Rene Schaefer
#------------------------------------------------------------------------------
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.counter                        import LineColumnCount, \
                                                         CountAction
from   quex.engine.state_machine.core             import StateMachine  
from   quex.engine.misc.interval_handling         import NumberSet, \
                                                         NumberSet_All
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.loop_counter                   import CountInfoMap, \
                                                         CountInfo
import quex.output.core.loop                      as     loop
from   quex.blackboard                            import E_CharacterCountType, \
                                                         setup as Setup
NS_A = NumberSet.from_range(ord('A'), ord('A') + 1)
NS_B = NumberSet.from_range(ord('B'), ord('B') + 1)
NS_C = NumberSet.from_range(ord('C'), ord('C') + 1)
NS_D = NumberSet.from_range(ord('D'), ord('D') + 1)

if "--hwut-info" in sys.argv:
    print "Loop: Get Loop Map."
    print "CHOICES: Plain, AppendixNoI, AppendixI, Split;"

def test(ci_list, SM_list=[]):
    Setup.buffer_codec.source_set = NumberSet_All()
    ci_map                     = CountInfoMap(ci_list, NumberSet.from_range(0, 100))
    iid_loop_exit              = dial_db.new_incidence_id()
    loop_map, appendix_sm_list = loop._get_loop_map(ci_map, SM_list, iid_loop_exit) 

    print
    print
    print
    general_checks(loop_map, appendix_sm_list)
    print_this(loop_map, appendix_sm_list)

def general_checks(loop_map, appendix_sm_list):
    print "#_[ Checks ]__________________________________________________"
    print
    print "character sets do not intersect",
    all_set = NumberSet()
    for lei in loop_map:
        assert lei.character_set is not None
        assert not lei.character_set.has_intersection(all_set)
        all_set.unite_with(lei.character_set)
    print "[ok]"

    print "count actions do not appear more than once",
    count_action_couple_set = set()
    count_action_plain_set  = set()
    exit_exists_f           = False
    appendix_sm_id_set      = set()
    for lei in loop_map:
        if lei.count_action is None: 
            assert lei.appendix_sm_id is None
            exit_exists_f = True
        elif lei.appendix_sm_id is None:
            assert lei.incidence_id not in count_action_plain_set
            count_action_plain_set.add(lei.incidence_id)
        else:
            assert lei.incidence_id not in count_action_couple_set
            count_action_couple_set.add(lei.incidence_id)
            appendix_sm_id_set.add(lei.appendix_sm_id)
    print "[ok]"
    list_id_set = set(sm.get_id() for sm in appendix_sm_list)
    assert appendix_sm_id_set == list_id_set
    print "appendix sm-ids are the same in loop map and sm list: [ok]"
    print "exit character set exits: [%s]" % exit_exists_f

    print

def print_this(loop_map, appendix_sm_list):
    print "#_[ Print ]___________________________________________________"
    print
    for lei in sorted(loop_map, key=lambda x: x.character_set.minimum()):
        print lei.character_set.get_string(Option="hex"), lei.incidence_id, lei.count_action,
        if lei.appendix_sm_id is None: print; continue
        print "<appendix: %s>" % lei.appendix_sm_id

    if not appendix_sm_list: return

    print
    print "#_[ Appendix State Machines ]________________________________"
    print
    for sm in sorted(appendix_sm_list, key=lambda sm: sm.get_id()):
        print "IncidenceId: %s" % sm.get_id()
        print sm
        print

def get_setup(L0, L1, FSM0, FSM1, FSM2):
    # SPECIALITIES: -- sm0 and sm1 have an intersection between their second 
    #                  transition.
    #               -- sm1 transits further upon acceptance.
    #               -- sm2 has only one transition.
    ci_list = [
        CountInfo(dial_db.new_incidence_id(), NumberSet.from_range(L0, L1), 
                  CountAction(E_CharacterCountType.COLUMN, 0)),
    ]

    # Generate State Machine that does not have any intersection with 
    # the loop transitions.
    sm0 = StateMachine()
    si = sm0.add_transition(sm0.init_state_index, FSM0)
    si = sm0.add_transition(si, NS_A, AcceptanceF=True)
    sm0.states[si].mark_acceptance_id(dial_db.new_incidence_id())

    sm1 = StateMachine()
    si0 = sm1.add_transition(sm1.init_state_index, FSM1)
    si  = sm1.add_transition(si0, NS_A, AcceptanceF=True)
    iid1 = dial_db.new_incidence_id()
    sm1.states[si].mark_acceptance_id(iid1)
    si  = sm1.add_transition(si, NS_B, si0)
    sm1.states[si].mark_acceptance_id(iid1)

    sm2 = StateMachine()
    si = sm2.add_transition(sm2.init_state_index, FSM2, AcceptanceF=True)
    sm2.states[si].mark_acceptance_id(dial_db.new_incidence_id())

    return ci_list, [sm0, sm1, sm2]

if "Plain" in sys.argv:
    # No parallel state machines
    test([
        CountInfo(0, NumberSet.from_range(0,    0x10), CountAction(E_CharacterCountType.COLUMN,     0)),
        CountInfo(1, NumberSet.from_range(0x20, 0x30), CountAction(E_CharacterCountType.LINE,       1)),
        CountInfo(2, NumberSet.from_range(0x40, 0x50), CountAction(E_CharacterCountType.GRID,       2)),
        CountInfo(3, NumberSet.from_range(0x60, 0x70), CountAction(E_CharacterCountType.WHITESPACE, 3)),
    ])

elif "AppendixNoI" in sys.argv:
    # Three state machines (no one intersects):
    # 
    # First Trans. sm0:         0x10-0x1F
    # First Trans. sm1:                   0x20-0x2F
    # First Trans. sm2:                             0x30-0x3F
    #
    ci_list, sm_list = get_setup(0x10, 0x40, 
                                 NumberSet.from_range(0x10, 0x20), 
                                 NumberSet.from_range(0x20, 0x30), 
                                 NumberSet.from_range(0x30, 0x40))

    for sm in sm_list:
        test(ci_list, [sm])
    test(ci_list, sm_list)

elif "AppendixI" in sys.argv:
    # Three state machines (no one intersects):
    # 
    # First Trans. sm0:         0x10 -               0x3F
    # First Trans. sm1:                0x20 -              0x4F
    # First Trans. sm2:                       0x30 -            0x5F
    #                           |  1  | 1&2  |   1&2&3   | 2&3 | 3  |  
    #
    ci_list, sm_list = get_setup(0x10, 0x60, 
                                 NumberSet.from_range(0x10, 0x40), 
                                 NumberSet.from_range(0x20, 0x50), 
                                 NumberSet.from_range(0x30, 0x60))

    # Test for each 'sm' in 'sm_list' is superfluous. 
    # It is done in 'AppendixNoI'.
    test(ci_list, sm_list)

elif "Split" in sys.argv:
    # A first transition of a state machine is separated into two, because
    # it is covered by more than one different count action.
    NS1 = NumberSet.from_range(0x10, 0x20)
    NS2 = NumberSet.from_range(0x20, 0x30)
    NS3 = NumberSet.from_range(0x30, 0x40)
    NS4 = NumberSet.from_range(0x40, 0x50)
    ci_list = [
        CountInfo(dial_db.new_incidence_id(), NS1, CountAction(E_CharacterCountType.COLUMN, 1)),
        CountInfo(dial_db.new_incidence_id(), NS2, CountAction(E_CharacterCountType.COLUMN, 2)),
        CountInfo(dial_db.new_incidence_id(), NS3, CountAction(E_CharacterCountType.COLUMN, 3)),
        CountInfo(dial_db.new_incidence_id(), NS4, CountAction(E_CharacterCountType.COLUMN, 4))
    ]

    sm  = StateMachine()
    si  = sm.init_state_index
    iid = dial_db.new_incidence_id()
    ti0 = sm.add_transition(si, NumberSet.from_range(0x1A, 0x4B))
    ac0 = sm.add_transition(ti0, NS_A, AcceptanceF=True)

    test(ci_list, [sm])
