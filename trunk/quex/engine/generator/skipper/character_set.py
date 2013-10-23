from   quex.engine.generator.base              import LoopGenerator
from   quex.engine.analyzer.door_id_address_label import DoorID
from   quex.engine.analyzer.state.core         import TerminalState
import quex.engine.analyzer.core                       as     analyzer_generator
from   quex.engine.input.files.counter_db      import CountCmdInfo
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

    NOTE: If dynamic character size codings, such as UTF8, are used as engine codecs,
          then the single state may actually be split into a real state machine of
          states.
    """
    def __init__(self, CharacterSet, CounterDb):
        assert not CharacterSet.is_empty()
        assert isinstance(CharacterSet, NumberSet)
        self.analyzer = None # Requires 'prepare_analyzer()'

        # If 'column_count_per_chunk' is not None, then reference positions may 
        # be used for counting (i.e. "column_n += (input_p - reference_p) * C").
        # This avoids 'column_n += C' at every single step.
        column_count_per_chunk = CounterDb.get_column_number_per_chunk(CharacterSet)

        # count_command_map:
        #
        #               map:  CLI -->  (NumberSet, CommandList)
        #
        # where the CommandList does the required column/line number counting 
        # for the given NumberSet. The tuple (NumberSet, CommandList) is
        # implemented as CountCmdInfo.
        self.count_command_map = CounterDb.get_counter_dictionary(CharacterSet, 
                                                                  column_count_per_chunk, 
                                                                  LanguageDB.INPUT_P)
        # on_entry/on_exit: 
        #
        # Actions to be performed at entry into the loop and when exiting.
        # 
        self.on_entry, \
        self.on_exit   = CounterDb.get_entry_exit_commands(LanguageDB.INPUT_P,
                                                           column_count_per_chunk)
        # on_before_reload/on_after_reload:
        #
        # Actions to be performed before and after reload.
        #
        self.on_before_reload, \
        self.on_after_reload   = CounterDb.get_reload_commands(LanguageDB.INPUT_P,
                                                               column_count_per_chunk)

        # The lexeme start pointer defines the lower border of memory to
        # be kept when reloading. Setting it to the input pointer allows
        # for the whole buffer to be reloaded.
        self.on_before_reload.append(LexemeStartToReferenceP(LanguageDB.INPUT_P))

    def prepare_analyzer(self, GlobalReloadStateForward):
        """
        The possibility of a dynamic character size codec forces to transform
        the single state into a state machine: 
        
                                        .----.    .---.
                                .-> ... | 11 |-->-| 1 |  line_n += 1;
                               +--> ... '----'    '---'   
                              +---> ... | 21 |-->--'|
                             +----> ... '----'      |
                    .------./           | 31 |-->---' 
                    | init |------> ... '----'                                     
                    '------'+-----> ...       
                             '----> ... 
                                     
        State '1' represents a counting action.  After the transformation is
        done, the structure can be transformed into a state machine where the
        transitions to '1' are bend into transitions to 'init'. It enters the
        'init' state at a door that inhibits the corresponding counting actions.
        
                        .-----------------------------------.
                        |                       .----.      |
                  .-(Door)------.       .-> ... | 11 |-->---| 
                  | line_n += 1 |      +--> ... '----'      |
                  '-------------'     +---> ... | 21 |-->---|
                        |            +----> ... '----'      |
                        |   .------./           | 31 |-->---' 
                        '-->| init |------> ... '----'                                     
                            '------'+-----> ...       
                                     '----> ... 
        """                                      
        sm       = self.get_counting_state_machine(self.count_command_map)
        transformation.do(sm)
        analyzer = analyzer_generator.do(sm, ReloadState=GlobalReloadStateForward)

        # (*) Entries _________________________________________________________
        #
        # This State: Create entries which execute required column/line 
        #             counting actions.
        loop = analyzer.init_state()
        for cli, count_info for self.count_command_map:
            assert isinstance(count_info, CountCmdInfo)
            for from_index in analyzer.to_db[cli]:
                loop.entry.enter(TransitionID(loop.index, from_index, TriggerId=cli), 
                                 TransitionAction(count_command_db[cli].clone()))

                self.bend(analyzer.state_db[from_index], to_index, self.index)

        tid_entry        = TransitionID(self.index, E_StateIndices.STATE_MACHINE_BEGIN)
        tid_after_reload = TransitionID(self.index, E_StateIndices.RELOAD_FORWARD)
        tid_exit         = TransitionID(self.index, index.get())
        loop.entry.enter(tid_entry,        TransitionAction(self.on_entry))
        loop.entry.enter(tid_after_reload, TransitionAction(self.on_after_reload))
        loop.entry.enter(tid_exit,         TransitionAction(self.on_exit))
        loop.entry.categorize()

        door_id_on_entry          = loop.entry.get(tid_entry).door_id
        door_id_on_exit           = loop.entry.get(tid_exit).door_id
        door_id_on_reload_success = loop.entry.get(tid_after_reload).door_id
        door_id_on_reload_failure = DoorID.global_terminal_end_of_file()

        # Reload State: Create an entry for this state upon reload.
        door_id_to_reload = analyzer.reload_state.add_state(self.index, 
                                                            door_id_on_reload_success, 
                                                            door_id_on_reload_failure,
                                                            BeforeReload=on_before_reload)

        # (*) Transition Map __________________________________________________
        #
        for state in analyzer.state_db.itervalues():
            state.transition_map.relate_to_DoorIDs(self.analyzer, state.index)
            state.transition_map.set_target(Setup.buffer_limit_code, door_id_to_reload)
            state.transition_map.fill_gaps(door_id_on_exit)

        return analyzer

        
    def get_code(self):
        # Build the skipper _______________________________________________________
        #
        analyzer = self.prepare_analyzer()
        return state_machine_coder.do(analyzer)

    def get_counting_state_machine(self, CommandListDb):
        sm = StateMachine(InitStateIndex=self.index)
        for cli, count_info in CommandListDb.iteritems():
            assert isinstance(count_info, CountCmdInfo)
            sm.add_transition(self.index, x.trigger_set, cli)
        return sm

    # Bend 'transition to target_i' to 'transition to door_i'
    def bend(interval, door_id):
        if  door_id.state_index in count_action_db:
            return (interval, DoorID(self.index, door_id.state_index))
        else:
            return (interval, door_id)

        for state in self.analyzer.state_db.iteritems():
            state.transition_map.relate_to_DoorIDs()
            state.transition_map = [ bend(interval, door_id) for interval, door_id in state.transition_map ]
