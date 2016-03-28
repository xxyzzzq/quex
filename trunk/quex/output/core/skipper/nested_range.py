from   quex.input.code.core                         import CodeTerminal
from   quex.output.core.variable_db                 import variable_db
from   quex.output.core.skipper.common              import get_character_sequence, \
                                                           get_on_skip_range_open, \
                                                           line_column_counter_in_loop
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.operations.operation_list        import Op
import quex.engine.state_machine.index              as     sm_index
from   quex.engine.state_machine.core               import StateMachine
from   quex.engine.loop_counter                     import LoopCountOpFactory
from   quex.engine.misc.interval_handling           import NumberSet_All
from   quex.engine.analyzer.door_id_address_label   import __nice, \
                                                           dial_db
from   quex.engine.analyzer.terminal.core           import Terminal
from   quex.engine.misc.string_handling             import blue_print
import quex.output.core.loop                        as     loop
from   quex.engine.misc.tools                       import typed
from   quex.blackboard                              import Lng, E_R

def do(Data, TheAnalyzer):

    CounterDb       = Data["counter_db"]
    OpenerSequence  = Data["opener_sequence"]
    CloserSequence  = Data["closer_sequence"]
    OnSkipRangeOpen = Data["on_skip_range_open"]
    DoorIdAfter     = Data["door_id_after"]

    return get_skipper(TheAnalyzer, OpenerSequence, CloserSequence, OnSkipRangeOpen, DoorIdAfter, CounterDb) 

def get_skipper(TheAnalyzer, OpenerSequence, CloserSequence, OnSkipRangeOpen, DoorIdAfter, CounterDb):
    """
                                    .---<---+----------<------+------------------.
                                    |       |                 |                  |
                                    |       | not             | open_n += 1      |  
                                  .------.  | Closer[0]       |                  |
       -------------------------->| Loop +--'                 |                  |
                                  |      |                    | yes              | 
                                  |      |                    |                  |
                                  |      |          .-------------.              |
                                  |      +----->----| Opener[1-N] |              |
                                  |      |          |      ?      |              |
                                  |      |          '-------------'              |
                                  |      |                                       | open_n > 0
                                  |      |          .-------------.              | 
                                  |      +----->----| Closer[1-N] |--------------+------> RESTART
                                  |      |          |      ?      | open_n -= 1    else
                                  |      |          '-------------'             
                                  |      |                             
                                  |  BLC +-->-.  
                              .->-|      |     \                 Reload State 
            .-DoorID(S, 1)--./    '------'      \            .------------------.
         .--| after_reload  |                    \          .---------------.   |
         |  '---------------'                     '---------| before_reload |   |
         |                                                  '---------------'   |
         '---------------------------------------------------|                  |
                                                     success '------------------'     
                                                                     | failure      
                                                                     |            
                                                              .---------------.       
                                                              | SkipRangeOpen |       
                                                              '---------------'                                                                   

    """
    psml             = _get_state_machine_vs_terminal_list(CloserSequence, 
                                                           OpenerSequence,
                                                           CounterDb, DoorIdAfter)
    count_op_factory = LoopCountOpFactory.from_ParserDataLineColumn(CounterDb, 
                                                                    NumberSet_All(), 
                                                                    Lng.INPUT_P()) 
    after_beyond     = [ 
        Op.GotoDoorId(DoorIdAfter) 
    ]

    result,          \
    door_id_beyond   = loop.do(count_op_factory,
                               AfterBeyond       = after_beyond,
                               LexemeEndCheckF   = False,
                               LexemeMaintainedF = False,
                               EngineType        = engine.FORWARD,
                               ReloadStateExtern = TheAnalyzer.reload_state,
                               ParallelSmTerminalPairList = psml) 

    counter_variable = Lng.REGISTER_NAME(E_R.Counter)
    variable_db.require(counter_variable)
    result[0:0] = "%s = 0;\n" % counter_variable
    return result

def _get_state_machine_vs_terminal_list(CloserSequence, OpenerSequence, CounterDb, DoorIdAfter): 
    """Additionally to all characters, the loop shall walk along the 'closer'.
    If the closer matches, the range skipping exits. Characters need to be 
    counted properly.

    RETURNS: list(state machine, terminal)

    The list contains only one single element.
    """
    # Opener Sequence Reaction
    opener_op_list = [
        Op.Increment(E_R.Counter)  
    ]
    # 'Goto loop entry' is added later (loop id unknown, yet).

    # Closer Sequence Reaction
    closer_op_list = [
        Op.Decrement(E_R.Counter),
        Op.GotoDoorIdIfCounterEqualZero(DoorIdAfter)
    ]
    # 'Goto loop entry' is added later (loop id unknown, yet).

    return [ 
        _get_state_machine_and_terminal(OpenerSequence, 
                                        "<SKIP NESTED RANGE OPENER>",
                                        opener_op_list),
        _get_state_machine_and_terminal(CloserSequence, 
                                        "<SKIP NESTED RANGE OPENER>",
                                        closer_op_list)
    ]

def _get_state_machine_and_terminal(Sequence, Name, OpList):
    """Create state machine that detects the 'Sequence', names the terminal
    with 'Name', and implements the 'CmdList' in the terminal.

    RETURNS: (state machine, terminal)
    """
    sm = StateMachine.from_sequence(Sequence)
    sm.set_id(dial_db.new_incidence_id())
    terminal = Terminal(CodeTerminal(Lng.COMMAND_LIST(OpList)), Name)
    terminal.set_incidence_id(sm.get_id())
    terminal.set_requires_goto_loop_entry_f()  # --> Goto Loop Entry

    return sm, terminal
