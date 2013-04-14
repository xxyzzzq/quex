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
    loop_txt,            = __make_loop(Mode, CharacterSet)

    # Build the skipper _______________________________________________________
    #
    result = __frame(loop_txt, CharacterSet, implementation_type, entry_action)

    return result

def __make_loop(Mode, CharacterSet):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop
    """
    LanguageDB = Setup.language_db

    # Determine 'column_count_per_chunk' before adding 'exit' and 'blc' 
    # characters.
    column_count_per_chunk = counter.get_column_number_per_chunk(Mode.counter_db, 
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
         counter.get_counter_map(Mode.counter_db, 
                                 IteratorName          = "me->buffer._input_p",
                                 ColumnCountPerChunk   = column_count_per_chunk,
                                 InsideCharacterSet    = CharacterSet,
                                 ExitCharacterSet      = exit_skip_set, 
                                 ReloadF               = True)

    tm = add_on_exit_actions(tm, exit_skip_set, implementation_type)

    after_reload_action.extend([
        1, "goto __SKIP;\n"
    ])


    # Prepare reload procedure, ensure transition to 'drop-out'
    transition_map_tool.set_target(tm, Setup.buffer_limit_code, 
                                   E_StateIndices.DROP_OUT)

    # 'BeforeReloadAction not None' forces a transition to RELOAD_PROCEDURE upon
    # buffer limit code.
    implementation_type, \
    loop_txt,            = CppGenerator.code_action_map(tm, 
                                        IteratorName       = "me->buffer._input_p", 
                                        BeforeReloadAction = before_reload_action, 
                                        AfterReloadAction  = after_reload_action,
                                        OnFailureAction    = None)

    return implementation_type, entry_action, loop_txt

def add_on_exit_actions(tm, ExitSkipSet, ImplementationType):
    """When a character appears which is not to be skipped, the loop must
    be quit. The loop exit is added to the given transition map 'tm' by 
    this function. Two things need to be considered:

    (1) Every character in 'ExitSkipSet' must cause an exit of the loop.

    (2) For those characters in 'ExitSkipSet' where there is no action
        yet, it may be necessary to append a "add(iterator-reference_p)".

    This is only necessary, if the column number can be derived from the 
    lexeme length. 
    """
    LanguageDB = Setup.language_db

    exit_action = [ 
        E_ActionIDs.ON_EXIT,
        1, "goto %s;" % get_label("$start", U=True)
    ]

    exit_tm = [
        (interval, exit_action) for interval in ExitSkipSet.get_intervals()
    ]

    # Before the content of transition maps can be added, the gaps need 
    # to be filled.
    transition_map_tool.fill_gaps(tm, [])
    transition_map_tool.fill_gaps(exit_tm, [])

    return transition_map_tool.add_transition_actions(tm, exit_tm)

def __frame(LoopTxt, CharacterSet, ImplementationType, EntryAction):
    """Implement the skipper."""
    LanguageDB = Setup.language_db

    comment = [1]
    LanguageDB.COMMENT(comment, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
    LanguageDB.INDENT(LoopTxt)

    # (*) Putting it all together _____________________________________________
    code = [ "__SKIP:\n" ]
    code.extend(comment)
    code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
    code.extend(EntryAction)
    code.extend([ 1, "while( 1 + 1 == 2 ) {\n" ])
    code.extend(LoopTxt)
    code.extend([ 1, "}\n"])

    return code

