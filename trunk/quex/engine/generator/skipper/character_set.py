from   quex.engine.generator.base              import LoopGenerator
from   quex.engine.analyzer.state.entry_action import DoorID
from   quex.engine.analyzer.state.core         import TerminalState
from   quex.blackboard                         import setup as Setup

class TerminalSkipCharacterSet(TerminalState):
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
    """
    def __init__(self, CharacterSet):
        assert not CharacterSet.is_empty()
        assert isinstance(CharacterSet, NumberSet)
        self.character_set             = CharacterSet
        self.index                     = index.get()
        self.door_id_loop_entry        = DoorID(skipper_state_index, 0)
        self.door_id_on_exit           = DoorID(skipper_state_index, 1)
        self.door_id_on_reload_success = DoorID(skipper_state_index, 2)
        self.door_id_on_reload_failure = DoorID.global_terminal_end_of_file()

        self.require_label_SKIP_f = None
        self.analyzer             = None
        self.counter_db           = None

    def materialize(self, TheAnalyzer, CounterDb, RequireSkipF):
        self.require_label_SKIP_f = RequireSkipF
        self.analyzer             = TheAnalyzer
        self.counter_db           = CounterDb

    def get_code(self):
        assert self.require_label_SKIP_f is not None
        assert self.analyzer is not None
        assert self.counter_db is not None
        assert type(require_label_SKIP_f) == bool

        # Implement the core loop _________________________________________________
        #
        transition_map, \
        column_count_per_chunk = Mode.counter_db.get_count_command_map()

        on_entry, on_exit = Mode.counter_db.get_entry_exit_Commands("me->buffer._input_p", 
                                                                    column_count_per_chunk)
        on_before_reload, on_after_reload = Mode.counter_db.get_reload_Commands("me->buffer._input_p", 
                                                                                column_count_per_chunk)

        # Character in 'CharacterSet' --> continue,
        transition_map.add_command_to_NotNone_targets(GotoDoorId(self.door_id_loop_entry))

        # On-Reload --> Reload State
        reload_door_id = analyzer.reload_state.add_state(self.index, 
                                                         self.door_id_on_reload_success, 
                                                         self.door_id_on_reload_failure,
                                                         BeforeReload=on_before_reload)

        transition_map.set_target(Setup.buffer_limit_code, reload_door_id)
        

        # Else --> Exit
        transition_map.replace_None_targets(self.door_id_on_exit)

        # Build the skipper _______________________________________________________
        #
        if RequireSKIPLabel:
            code.append("__SKIP:\n")
        code.append(1)
        LanguageDB.COMMENT(code, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
        code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
        code(on_entry)
        code(dial_db.map_door_id_to_label(loop_start_door_id))
        code(transition_map)
        code(dial_db.map_door_id_to_label(exit_door_id))
        code(on_exit)
        code(dial_db.map_door_id_to_label(on_reload_success_door_id))
        code(on_after_reload)
        code(LanguageDB.GOTO_BY_DOOR_ID(loop_start_door_id))
        return result

