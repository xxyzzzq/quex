import quex.engine.generator.state.entry as entry
from   quex.blackboard import Lng, \
                              E_StateIndices

def do(TheReloadState):
    assert TheReloadState.index in (E_StateIndices.RELOAD_FORWARD, \
                                    E_StateIndices.RELOAD_BACKWARD)
    assert TheReloadState.entry.size() != 0

    txt, post_txt = entry.do(TheReloadState)
    assert not post_txt

    txt.extend(
        Lng.RELOAD_PROCEDURE(ForwardF=(TheReloadState.index == E_StateIndices.RELOAD_FORWARD))
    )
    return txt

