from   quex.engine.generator.base                   import LoopGenerator
from   quex.engine.generator.languages.address      import get_label
from   quex.blackboard                              import setup as Setup

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
    NOTE: The 'range skipper' takes care that it transits immediately to 
    the indentation handler, if it ends on 'newline'. This is not necessary
    here. Quex refuses to work on 'skip sets' when they match common lexemes
    with the indentation handler.
    ___________________________________________________________________________
    """
    CharacterSet         = Data["character_set"]
    require_label_SKIP_f = Data["require_label_SKIP_f"]

    assert CharacterSet.__class__.__name__ == "NumberSet"
    assert not CharacterSet.is_empty()
    assert type(require_label_SKIP_f) == bool

    # Implement the core loop _________________________________________________
    #
    implementation_type, \
    loop_txt,            \
    entry_action,        \
    exit_action          = LoopGenerator.do(Mode.counter_db, 
                             IteratorName = "me->buffer._input_p",
                             OnContinue   = [ 1, "continue;" ],
                             OnExit       = [ 1, "goto %s;" % get_label("$start", U=True) ],
                             CharacterSet = CharacterSet, 
                             ReloadF      = True)

    # Build the skipper _______________________________________________________
    #
    result = __frame(implementation_type, loop_txt, 
                     CharacterSet, entry_action, require_label_SKIP_f)

    return result

def __frame(ImplementationType, LoopTxt, CharacterSet, EntryAction, RequireSKIPLabel):
    """Implement the skipper."""
    LanguageDB = Setup.language_db

    LanguageDB.INDENT(LoopTxt)

    code = []
    if RequireSKIPLabel:
        code.append("__SKIP:\n")
    code.append(1)
    LanguageDB.COMMENT(code, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
    code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
    code.extend(EntryAction)
    code.extend([ 1, "while( 1 + 1 == 2 ) {\n" ])
    code.extend(LoopTxt)
    code.extend([ 1, "}\n"])

    return code

