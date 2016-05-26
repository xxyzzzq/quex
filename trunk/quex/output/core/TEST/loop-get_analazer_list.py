# TEST: Generate all Analyzer-s based on a given LoopMap
#
# This test calls '_get_analyzer_list()' to generate a list of analyzers
# related to a loop map. 
#
# UNIMPORTANT:
#
#      -- The structure of the analyzers in the list is unimportant;
#         none of them is modified.
#      -- The loop maps constitutition is (almost) unimportant. 
#
# IMPORTANT:
#
#      -- The loop analyzer implements the loop map correctly. 
#      -- All appendix state machines are translated into analyzers.
#      -- For counting, the counting behavior differs if the number 
#         of code units per character is constant or not.
#      => use same loop map for all analyzers.
# 
# Variations: Column Number per CodeUnit = const. or not.
#             Number of CodeUnits per Character = const. or not.
#
# Both variations are played through by the 'buffer_codec' being plain Unicode
# or UTF8, thus the choices: 'Unicode' and 'UTF8'. Additionally, two loop maps
# are presented: One with same 'ColumnN/CodeUnit' for all characters and one 
# without it.
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
import quex.engine.state_machine.transformation.core as  bc_factory
import quex.engine.analyzer.engine_supply_factory as     engine
import quex.output.core.loop                      as     loop
from   quex.output.core.loop                      import LoopMapEntry, \
                                                         LoopEventHandlers
from   quex.blackboard                            import E_CharacterCountType, \
                                                         setup as Setup
if "--hwut-info" in sys.argv:
    print "Loop: Get All Analyzers."
    print "CHOICES: Unicode-Const, Unicode-NonConst, UTF8-Const, UTF8-NonConst;"

if "Unicode" in sys.argv[1]:  encoding = "unicode"
else:                         encoding = "utf8"

# Constant column number per code unit
if "NonConst" in sys.argv[1]: column_n_per_code_unit = None
else:                         column_n_per_code_unit = 6     # See CA_0, below.

def test(LoopMap, EventHandler):
    """
    event_handler:    Simply, some event handlers are generated which allow to
                      identify their placement in the right positions.
    
    appendix_sm_list: The shape of the state machines is completely irrelevant 
                      for this test. So, for all mentioned state machines a 
                      trivial single transition state machine is generated on 
                      the fly.
    """
    global loop_map

    Setup.buffer_codec.source_set = NumberSet_All()

    appendix_sm_list = _get_appendix_sm_list(loop_map)

    analyzer_list    = loop._get_analyzer_list(loop_map,
                                               EventHandler, 
                                               appendix_sm_list) 

    print_this(analyzer_list)

def _get_appendix_sm_list(LoopMap):
    def get_sm(SmId, Trigger):
        sm = StateMachine.from_IncidenceIdMap([
            (NumberSet.from_range(Trigger, Trigger + 1), SmId)
        ])
        sm.set_id(SmId)
        return sm

    return [
        get_sm(lei.appendix_sm_id, trigger) for trigger, lei in enumerate(LoopMap)
        if lei.appendix_sm_has_transitions_f
    ]

def print_this(AnalyzerList):
    print "#_[ Print %i analyzer(s) ]______________________________" % len(AnalyzerList)
    print
    for i, analyzer in enumerate(AnalyzerList):
        print "--( %i: init si = %i )-------------------------\n" % (i, analyzer.init_state_index)
        print analyzer

if encoding == "unicode":
    NS_A = NumberSet.from_range(ord('A'), ord('A') + 1)
    NS_B = NumberSet.from_range(ord('B'), ord('B') + 1)
    NS_C = NumberSet.from_range(ord('C'), ord('C') + 1)
    NS_D = NumberSet.from_range(ord('D'), ord('D') + 1)
    NS_E = NumberSet.from_range(ord('E'), ord('E') + 1)
else:
    NS_A = NumberSet.from_range(0x600, 0x601)
    NS_B = NumberSet.from_range(0x601, 0x602)
    NS_C = NumberSet.from_range(0x602, 0x603)
    NS_D = NumberSet.from_range(0x603, 0x604)
    NS_E = NumberSet.from_range(0x604, 0x605)

CA_0 = CountAction(E_CharacterCountType.COLUMN,     5)
CA_1 = CountAction(E_CharacterCountType.LINE,       1)
CA_2 = CountAction(E_CharacterCountType.GRID,       2)
CA_3 = CountAction(E_CharacterCountType.WHITESPACE, 3)
CA_4 = CountAction(E_CharacterCountType.WHITESPACE, 4)

# Mini Appendix Sm-s are generated during the test.
appendix_sm_id_0 = 815L
appendix_sm_id_1 = 4711L
appendix_sm_id_2 = 33L

#______________________________________________________________________________
#
# CHOICE: --> encoding
#         --> column_n_per_code_unit
#
Setup.buffer_codec_set(bc_factory.do(encoding), LexatomSizeInBytes=1)

event_handler = LoopEventHandlers(column_n_per_code_unit, 
                                  MaintainLexemeF   = False, 
                                  LexemeEndCheckF   = False, 
                                  EngineType        = engine.FORWARD, 
                                  ReloadStateExtern = None, 
                                  UserOnLoopExit    = [])

loop_map = [
    LoopMapEntry(NS_A, CA_0, CA_0.get_incidence_id(), None),
    LoopMapEntry(NS_B, CA_1, CA_1.get_incidence_id(), appendix_sm_id_0, HasTransitionsF=True),
    LoopMapEntry(NS_C, CA_2, CA_2.get_incidence_id(), appendix_sm_id_0, HasTransitionsF=True),
    LoopMapEntry(NS_D, CA_3, CA_0.get_incidence_id(), appendix_sm_id_1),
    LoopMapEntry(NS_E, CA_4, CA_4.get_incidence_id(), appendix_sm_id_2, HasTransitionsF=False)
]

test(loop_map, event_handler)
