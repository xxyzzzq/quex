import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.generator.base                   import Generator as CppGenerator
from   quex.engine.generator.languages.address      import get_label, \
                                                           address_set_subject_to_routing_add
from   quex.engine.generator.languages.variable_db  import variable_db
import quex.output.cpp.counter                      as     counter
from   quex.blackboard                              import setup as Setup, \
                                                           E_StateIndices, \
                                                           E_ActionIDs, \
                                                           E_MapImplementationType
from   quex.engine.interval_handling                import NumberSet, Interval
import quex.engine.analyzer.transition_map          as     transition_map_tool

def do(Data, Mode):
    """________________________________________________________________________
    Generate a character set skipper state. As long as characters of a given
    character set appears it iterates to itself:

                                 input in Set
                                   .--<---.
                                  |       |
                              .-------.   |
                   --------->( SKIPPER )--+----->------> RESTART
                              '-------'       input 
                                            not in Set
    ___________________________________________________________________________
    """
    CharacterSet         = Data["character_set"]
    require_label_SKIP_f = Data["require_label_SKIP_f"]

    assert CharacterSet.__class__.__name__ == "NumberSet"
    assert not CharacterSet.is_empty()
    assert type(require_label_SKIP_f) == bool

    get_label("$state-router", U=True)             # 'reload' req. state router

    # Implement the core loop _________________________________________________
    #
    implementation_type, \
    entry_action,        \
    loop_txt,            = __make_loop(Mode.counter_db, CharacterSet)

    # Build the skipper _______________________________________________________
    #
    result = __frame(loop_txt, CharacterSet, implementation_type, entry_action, require_label_SKIP_f)

    return result

def __make_loop(CounterDB, CharacterSet):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop
    """
    LanguageDB = Setup.language_db

    # Determine 'column_count_per_chunk' before adding 'exit' and 'blc' 
    # characters.
    column_count_per_chunk = counter.get_column_number_per_chunk(CounterDB,
                                                                 CharacterSet)

    # Possible reactions on a character _______________________________________
    #
    blc_set       = NumberSet(Setup.buffer_limit_code)
    skip_set      = CharacterSet.clone()
    skip_set.subtract(blc_set)
    exit_skip_set = CharacterSet.inverse()
    exit_skip_set.subtract(blc_set)

    #  Buffer Limit Code --> Reload
    #  Skip Character    --> Loop to Skipper State
    #  Else              --> Exit Loop

    # Implement the core loop _________________________________________________
    tm,                     \
    implementation_type,    \
    entry_action,           \
    before_reload_action,   \
    after_reload_action =   \
         counter.get_counter_map(CounterDB,
                                 IteratorName          = "me->buffer._input_p",
                                 ColumnCountPerChunk   = column_count_per_chunk,
                                 InsideCharacterSet    = CharacterSet,
                                 ExitCharacterSet      = exit_skip_set, 
                                 ReloadF               = True)

    transition_map_tool.insert_after_action_id(tm, E_ActionIDs.ON_EXIT,
                                               [ 1, "goto %s;" % get_label("$start", U=True) ])
    transition_map_tool.insert_after_action_id(tm, E_ActionIDs.ON_GOOD_TRANSITION,
                                               [ 1, "continue;" ])

    # 'BeforeReloadAction not None' forces a transition to RELOAD_PROCEDURE upon
    # buffer limit code.
    implementation_type, \
    loop_txt,            = CppGenerator.code_action_map(tm, 
                                        IteratorName       = "me->buffer._input_p", 
                                        BeforeReloadAction = before_reload_action, 
                                        AfterReloadAction  = after_reload_action,
                                        OnFailureAction    = None)

    return implementation_type, entry_action, loop_txt

def __frame(LoopTxt, CharacterSet, ImplementationType, EntryAction, RequireSKIPLabel):
    """Implement the skipper."""
    LanguageDB = Setup.language_db

    comment = [1]
    LanguageDB.COMMENT(comment, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
    LanguageDB.INDENT(LoopTxt)

    # (*) Putting it all together _____________________________________________
    code = [ ]
    if RequireSKIPLabel:
        code.append("__SKIP:\n")
    code.extend(comment)
    code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
    code.extend(EntryAction)
    code.extend([ 1, "while( 1 + 1 == 2 ) {\n" ])
    code.extend(LoopTxt)
    code.extend([ 1, "}\n"])

    return code

