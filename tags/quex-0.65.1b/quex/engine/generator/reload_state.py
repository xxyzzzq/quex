import quex.engine.generator.state.entry as entry
from   quex.blackboard import Lng, \
                              E_StateIndices

def do(TheReloadState):
    

    if TheReloadState.entry.size() == 0:
        return []

    txt = ["%s\n" % Lng.UNREACHABLE]

    entry.do_core(txt, TheReloadState)

    assert TheReloadState.index in (E_StateIndices.RELOAD_FORWARD, E_StateIndices.RELOAD_BACKWARD)
    txt.extend(
        Lng.RELOAD_PROCEDURE(ForwardF=(TheReloadState.index == E_StateIndices.RELOAD_FORWARD))
    )
    return txt

