import quex.engine.generator.state.entry as entry
from   quex.blackboard import setup as Setup, \
                              E_StateIndices

def do(TheReloadState):
    LanguageDB = Setup.language_db

    if TheReloadState.entry.size() == 0:
        return []

    txt = ["%s\n" % LanguageDB.UNREACHABLE]

    entry.do_core(txt, TheReloadState)

    assert TheReloadState.index in (E_StateIndices.RELOAD_FORWARD, E_StateIndices.RELOAD_BACKWARD)
    txt.extend(LanguageDB.RELOAD_PROCEDURE(ForwardF=(TheReloadState.index == E_StateIndices.RELOAD_FORWARD)))

    return txt

