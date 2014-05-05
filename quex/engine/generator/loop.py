from   quex.engine.generator.languages.variable_db     import variable_db
import quex.engine.generator.base                      as     generator
from   quex.engine.analyzer.terminal.core              import Terminal
from   quex.engine.generator.code.core                 import CodeTerminal
from   quex.engine.analyzer.state.entry_action         import TransitionAction
from   quex.engine.state_machine.engine_state_machine_set import CharacterSetStateMachine
from   quex.engine.analyzer.state.drop_out             import DropOutGotoDoorId
import quex.engine.analyzer.core                       as     analyzer_generator
import quex.engine.analyzer.engine_supply_factory      as     engine
from   quex.engine.analyzer.commands.core                   import E_R, \
                                                              CommandList, \
                                                              Assign, \
                                                              GotoDoorId
import quex.engine.state_machine.index                 as     index
from   quex.engine.tools                               import typed
from   quex.engine.analyzer.door_id_address_label      import DoorID, \
                                                              dial_db
from   quex.blackboard import E_StateIndices, \
                              setup as Setup, \
                              Lng, \
                              E_Cmd


@typed(ReloadF=bool, LexemeEndCheckF=bool, DoorIdExit=DoorID)
def do(CcFactory, DoorIdExit, LexemeEndCheckF=False, ReloadF=False, ReloadStateExtern=None, LexemeMaintainedF=False):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop

    NOTE: This function does NOT code the FAILURE terminal. The caller needs to 
          do this if required.

    Generate code to iterate over the input stream until

           -- A character occurs not in CharacterSet, or
           -- [optional] the 'LexemeEnd' is reached.

    That is, simplified:
                             input in Set
                             .--<--.
                            |      |  LexemeEnd
                            |      +----->------> (Exit)
                          .----.   |
               --------->( Loop )--+----->------> Exit
                          '----'       input 
                                     not in Set
        
    At the end of the iteration, the 'input_p' points to (the begin of) the
    first character which is not in CharacterSet (or the LexemeEnd).

            [i][i][i]..................[i][i][X][.... 
                                             |
                                          input_p
            
    During the 'loop' possible line/column count commands may be applied. To
    achieve the iteration, a simplified pattern matching engine is implemented:

              transition
              map
              .------.  
              |  i0  |----------> Terminal0: CommandList0   
              +------+
              |  i1  |----------> Terminal1: CommandList1   
              +------+
              |  X2  |----------> Terminal Beyond: input_p--; goto TerminalExit;
              +------+
              |  i2  |----------> Terminal2: CommandList2
              +------+
    """
    assert ReloadF or ReloadStateExtern is None

    # (*) Construct State Machine and Terminals _______________________________
    #
    CsSm, beyond_iid = get_CharacterSetStateMachine(CcFactory, LexemeMaintainedF)

    analyzer = analyzer_generator.do(CsSm.sm, engine.FORWARD, ReloadStateExtern)
    analyzer.init_state().drop_out = DropOutGotoDoorId(DoorIdExit)

    door_id_loop = _prepare_entry_and_reentry(analyzer, CcFactory, CsSm) 

    if not LexemeEndCheckF: door_id_on_lexeme_end = None
    else:                   door_id_on_lexeme_end = DoorIdExit

    # -- Analyzer: Prepare Reload
    if ReloadF:
        _prepare_reload(analyzer, CcFactory, CsSm, ReloadStateExtern)

    # -- The terminals 
    #
    terminal_list   = CcFactory.get_terminal_list(Lng.INPUT_P(), 
                                                  DoorIdOk          = door_id_loop, 
                                                  DoorIdOnLexemeEnd = door_id_on_lexeme_end)

    terminal_list.append(get_terminal_beyond(CsSm, CcFactory, DoorIdExit, beyond_iid))

    # (*) Generate Code _______________________________________________________
    txt = []
    txt.extend(generator.do_analyzer(analyzer))
    txt.extend(generator.do_terminals(terminal_list, analyzer))
    if ReloadF:
        txt.extend(generator.do_reload_procedure(analyzer))

    if CcFactory.requires_reference_p():   variable_db.require("reference_p")
    if Setup.variable_character_sizes_f(): variable_db.require("character_begin_p")
    
    return txt, DoorID.incidence(beyond_iid)

def _prepare_entry_and_reentry(analyzer, CcFactory, CsSm):
    """Prepare the entry and re-entry doors into the initial state
    of the loop-implementing initial state.

                   .----------.
                   | on_entry |
                   '----------'
                        |         .------------.
                        |<--------| on_reentry |<-----.
                        |         '------------'      |
                .----------------.                    |
                |                +-----> Terminal ----+----> Exit
                |      ...       |
                |                +-----> Terminal - - 
                '----------------'

       RETURNS: DoorID of the re-entry door which is used to iterate in 
                the loop.
    """
    # Entry into state machine
    entry            = analyzer.init_state().entry
    init_state_index = analyzer.init_state_index
        
    # OnEntry
    ta_on_entry              = entry.get_action(init_state_index, E_StateIndices.NONE)
    ta_on_entry.command_list = CommandList.concatinate(ta_on_entry.command_list, 
                                                       CsSm.on_begin + CcFactory.on_begin)

    # OnReEntry
    tid_reentry = entry.enter(init_state_index, index.get(), 
                              TransitionAction(CommandList.from_iterable(CsSm.on_begin)))
    entry.categorize(init_state_index)

    return entry.get(tid_reentry).door_id

def get_CharacterSetStateMachine(CcFactory, LexemeMaintainedF, ParallelSmList=None):
    """Takes a character counting factory and produces a state machine out
    of it.
    """
    beyond_set = CcFactory.character_set.inverse().mask(0, Setup.get_character_value_limit())

    incidence_id_map = CcFactory.get_incidence_id_map()

    beyond_iid = dial_db.new_incidence_id()
    incidence_id_map.append((beyond_set, beyond_iid))

    # Build a state machine based on (character set, incidence_id) pairs.
    ccsm = CharacterSetStateMachine(incidence_id_map, LexemeMaintainedF, ParallelSmList)
    return ccsm, beyond_iid

def _prepare_reload(analyzer, CcFactory, CsSm, ReloadStateExtern): 
        
    on_before_reload = CommandList.from_iterable(
           CsSm.on_before_reload
         + CcFactory.on_before_reload
    )
#    def debuggey(Name, Cl):
#        print "#Nam:", Name
#        for cmd in Cl:
#            print "#  ", str(cmd)
#    debuggey("CcFactor", CcFactory.on_after_reload)
#    debuggey("CsSm", CsSm.on_after_reload)
    on_after_reload  = CommandList.from_iterable(
          CsSm.on_after_reload
        + CcFactory.on_after_reload
    )

    analyzer_generator.prepare_reload(analyzer, on_before_reload, on_after_reload)

def get_terminal_beyond(CsSm, CcFactory, DoorIdExit, BeyondIid, AdditionalCommandList=None):
    """Generate Terminal to be executed upon exit from the 'loop'.
    
       CcFactory  -- Determines what is to to be done upon exit from the 'loop'.
       DoorIdExit -- DoorId where to go after the terminal has finished.
       BeyondIid  -- 'Beyond Incidence Id', that is the incidencen id if of
                     the terminal to be generated.
    """
    on_beyond = []
    on_beyond.extend(CsSm.on_putback)
    on_beyond.extend(CcFactory.on_end)
    if AdditionalCommandList is not None:
        on_beyond.extend(AdditionalCommandList)
    on_beyond.append(GotoDoorId(DoorIdExit))

    code_on_beyond  = CodeTerminal([Lng.COMMAND(cmd) for cmd in on_beyond])

    result = Terminal(code_on_beyond, "<BEYOND>") # Put last considered character back
    result.set_incidence_id(BeyondIid)

    return result

