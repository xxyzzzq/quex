from   quex.engine.generator.languages.variable_db     import variable_db
import quex.engine.generator.base                      as     generator
from   quex.engine.analyzer.terminal.core              import Terminal
from   quex.engine.generator.code.core                 import CodeTerminal
from   quex.engine.analyzer.state.entry_action         import TransitionAction
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
def do(CcFactory, DoorIdExit, LexemeEndCheckF=False, EngineType=None, ReloadStateExtern=None, LexemeMaintainedF=False):
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
    assert EngineType is not None
    # NOT: assert (not EngineType.subject_to_reload()) or ReloadStateExtern is None
    # This would mean, that the user has to make these kinds of decisions. But, 
    # we are easily able to ignore meaningless ReloadStateExtern objects.

    # (*) Construct State Machine and Terminals _______________________________
    #
    CsSm, beyond_iid = CcFactory.get_CharacterSetStateMachine(LexemeMaintainedF)

    analyzer = analyzer_generator.do(CsSm.sm, EngineType,
                                     ReloadStateExtern,
                                     OnBeforeReload = CommandList.from_iterable(CsSm.on_before_reload), 
                                     OnAfterReload  = CommandList.from_iterable(CsSm.on_after_reload))

    analyzer.drop_out.entry.enter_CommandList(
        E_StateIndices.DROP_OUT, analyzer.init_state_index, 
        CommandList(GotoDoorId(DoorIdExit))
    )
    analyzer.drop_out.entry.categorize(E_StateIndices.DROP_OUT)

    door_id_loop = _prepare_entry_and_reentry(analyzer, CsSm.on_begin, CsSm.on_step) 

    if not LexemeEndCheckF: door_id_on_lexeme_end = None
    else:                   door_id_on_lexeme_end = DoorIdExit

    # -- The terminals 
    #
    terminal_list = CcFactory.get_terminal_list(CsSm.on_end, beyond_iid,
                                                DoorIdExit,
                                                DoorIdOk          = door_id_loop, 
                                                DoorIdOnLexemeEnd = door_id_on_lexeme_end)

    # (*) Generate Code _______________________________________________________
    txt = _get_source_code(CcFactory, analyzer, terminal_list)
    
    return txt, DoorID.incidence(beyond_iid)

def _prepare_entry_and_reentry(analyzer, OnBegin, OnStep):
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
                                                       OnBegin)

    # OnReEntry
    tid_reentry = entry.enter_CommandList(init_state_index, index.get(), 
                                          CommandList.from_iterable(OnStep))
    entry.categorize(init_state_index)

    return entry.get(tid_reentry).door_id

def _get_source_code(CcFactory, analyzer, terminal_list):
    """RETURNS: String containing source code for the 'loop'. 

       -- The source code for the (looping) state machine.
       -- The terminals which contain counting actions.

    Also, it requests variable definitions as they are required.
    """
    txt = []
    txt.extend(generator.do_analyzer(analyzer))
    txt.extend(generator.do_terminals(terminal_list, analyzer))
    if analyzer.engine_type.subject_to_reload():
        txt.extend(generator.do_reload_procedure(analyzer))

    if CcFactory.requires_reference_p():   variable_db.require("reference_p")
    if Setup.variable_character_sizes_f(): variable_db.require("character_begin_p")
    return txt
