from   quex.engine.counter                        import CountCmdFactory
from   quex.engine.analyzer.state.core            import Processor
from   quex.engine.analyzer.commands.core         import GotoDoorId

import quex.engine.generator.loop                 as     loop
import quex.engine.analyzer.engine_supply_factory as     engine
from   quex.engine.analyzer.door_id_address_label import DoorID
from   quex.blackboard                            import setup as Setup, \
                                                         Lng

def do(Data, TheAnalyzer):
    """Fast implementation of character set skipping machine.
    ________________________________________________________________________
    As long as characters of a given character set appears it iterates: 

                                 input in Set
                                   .--<---.
                                  |       |
                              .-------.   |
                   --------->( SKIPPER )--+----->------> RESTART
                              '-------'       input 
                                            not in Set

    ___________________________________________________________________________
    NOTE: The 'TerminalSkipRange' takes care that it transits immediately to 
    the indentation handler, if it ends on 'newline'. This is not necessary
    for 'TerminalSkipCharacterSet'. Quex refuses to work on 'skip sets' when 
    they match common lexemes with the indentation handler.
    ___________________________________________________________________________

    Precisely, i.e. including counter and reload actions:

    START
      |
      |    .----------------------------------------------.
      |    |.-------------------------------------------. |
      |    ||.----------------------------------------. | |
      |    |||                                        | | |
      |    |||  .-DoorID(S, a)--.    transition       | | |
      |    || '-|  gridstep(cn) |       map           | | |        
      |    ||   '---------------'\    .------.        | | |        
      |    ||   .-DoorID(S, b)--. '->-|      |        | | |       
      |    |'---|  ln += 1      |--->-| '\t' +-->-----' | |      
      |    |    '---------------'     |      |          | |     
      |    |    .-DoorID(S, c)--.     | ' '  +-->-------' |   
      |    '----|  cn += 1      |--->-|      |            |   
      |         '---------------'     | '\n' +-->---------'              
      |                               |      |                  .-DropOut ------.        
      |         .-DoorID(S, 0)--.     | else +-->---------------| on_exit       |                                
      '------>--| on_entry      |--->-|      |                  '---------------'        
                '---------------'     |  BLC +-->-.  
                                  .->-|      |     \                 Reload State 
                .-DoorID(S, 1)--./    '------'      \             .-----------------.
           .----| after_reload  |                    \          .---------------.   |
           |    '---------------'                     '---------| before_reload |   |
           |                                                    '---------------'   |
           '-----------------------------------------------------|                  |
                                                         success '------------------'     
                                                                         | failure      
                                                                         |            
                                                                  .---------------.       
                                                                  | End of Stream |       
                                                                  '---------------'                                                                   

    NOTE: If dynamic character size codings, such as UTF8, are used as engine codecs,
          then the single state may actually be split into a real state machine of
          states.
    """
    counter_db    = Data["counter_db"]
    character_set = Data["character_set"]

    if Setup.buffer_based_analyzis_f:
        reload_state = None
        reload_f     = False
    else:
        reload_state = TheAnalyzer.reload_state
        reload_f     = True
        
    result, \
    door_id_beyond = loop.do(CountCmdFactory.from_ParserDataLineColumn(counter_db, character_set, Lng.INPUT_P()), 
                             AfterBeyond       = [ GotoDoorId(DoorID.continue_without_on_after_match()) ],
                             LexemeEndCheckF   = False,
                             LexemeMaintainedF = False,
                             EngineType        = engine.FORWARD,
                             ReloadStateExtern = reload_state) 

    assert isinstance(result, list)
    return result
