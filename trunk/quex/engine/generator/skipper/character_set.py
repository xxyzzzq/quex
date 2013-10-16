from   quex.engine.generator.base              import LoopGenerator
from   quex.engine.analyzer.door_id_address_label import DoorID
from   quex.engine.analyzer.state.core         import TerminalState
from   quex.blackboard                         import setup as Setup

def do():
    """________________________________________________________________________
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
    """
    def __init__(self, CharacterSet, require_label_SKIP_f, analyzer, counter_db):
        assert not CharacterSet.is_empty()
        assert isinstance(CharacterSet, NumberSet)
        self.index          = index.get()
        self.door_id_entry  = DoorID(self.index, 0)
        door_id_drop_out    = DoorID.drop_out(self.index)

        self.transition_map = None

        # -- counter_db.get_count_command_map() delivers:
        #
        #               map:  interval ---> CLI
        #
        # where 'count_command_db[CLI]' is the CommandList which does the required
        # column/line number counting for the given character interval.
        # 
        # If 'column_count_per_chunk' is not None, then reference positions may 
        # be used for counting (i.e. "column += (input_p - reference_p) * C").
        count_map, count_command_db, \
        column_count_per_chunk            = Mode.counter_db.get_count_command_map()
        on_entry, on_exit                 = Mode.counter_db.get_entry_exit_Commands(LanguageDB.INPUT_P,
                                                                                    column_count_per_chunk)
        on_before_reload, on_after_reload = Mode.counter_db.get_reload_Commands(LanguageDB.INPUT_P,
                                                                                column_count_per_chunk)

        def trid(CLI): 
            return TransitionID(self.index, self.index, CLI) 
        
        # (*) Entries _________________________________________________________
        #
        # This State: Create entries which execute required column/line 
        #             counting actions.
        for interval, CLI in count_map:
            ta = TransitionAction(CommandListF=False)
            ta.command_list = count_command_db[CLI].clone()
            self.entry.action_db.enter(trid(self.index, self.index, TriggerId=CLI), ta)

        # Setting the lexeme start = input pointer makes it possible to load the whole buffer.
        on_after_reload.append(LexemeStartToReferenceP(LanguageDB.INPUT_P))
        ta = TransitionAction(CommandListF=False)
        ta.command_list = on_after_reload
        self.entry.action_db.enter(TransitionID(self.index, E_StateIndices.RELOAD_FORWARD), ta)
        self.entry.action_db.categorize()

        door_id_on_reload_success = self.entry.action_db.get_door_id(self.index, E_StateIndices.RELOAD_FORWARD)
        door_id_on_reload_failure = DoorID.global_terminal_end_of_file()

        # Reload State: Create an entry for this state upon reload.
        reload_door_id = analyzer.reload_state.add_state(self.index, 
                                                         door_id_on_reload_success, 
                                                         door_id_on_reload_failure,
                                                         BeforeReload=on_before_reload)

        # (*) Transition Map __________________________________________________
        #
        #     map: interval --> entry where column/lines are counted.
        #          BLC      --> entry into reload state.
        #
        self.transition_map = TransitionMap.from_iterable(count_map, trid)
        self.transition_map.set_target(Setup.buffer_limit_code, reload_door_id)

        class PseudoAnalyzer:
            def __init__(self, StateIndex, State): self.state_db = { StateIndex: State }

        self.relate_to_DoorIDs(PseudoAnalyzer(self.index, self), self.index)
        
        # (*) DropOut _________________________________________________________
        #
        self.on_drop_out = on_exit

    def get_code(self):
        # Build the skipper _______________________________________________________
        #
        if RequireSKIPLabel:
            code.append("__SKIP:\n")
        code.append(1)
        LanguageDB.COMMENT(code, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
        code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
        code(on_entry)
        code(dial_db.get_label_by_door_id(self.door_id_loop_entry))
        code(transition_map) # input in CharacterSet => goto door_id_loop_entry
        #                    # else                  => exit, i.e. drop into below
        code(dial_db.get_label_by_door_id(exit_door_id))
        code(on_exit)
        code(dial_db.get_label_by_door_id(on_reload_success_door_id))
        code(on_after_reload)
        code(LanguageDB.GOTO_BY_DOOR_ID(self.door_id_loop_entry))
        return result

