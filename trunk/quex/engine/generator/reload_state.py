import quex.engine.generator.state.entry as entry
from   quex.blackboard import Lng, \
                              E_StateIndices

def do(TheReloadState):
    assert TheReloadState.index in (E_StateIndices.RELOAD_FORWARD, \
                                    E_StateIndices.RELOAD_BACKWARD)
    assert TheReloadState.entry.size() != 0

    pre_txt, txt = entry.do(TheReloadState)
    assert pre_txt is None

    txt.extend(
        Lng.RELOAD_PROCEDURE(ForwardF=(TheReloadState.index == E_StateIndices.RELOAD_FORWARD))
    )
    return txt

