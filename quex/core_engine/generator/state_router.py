from quex.input.setup import setup as Setup
from operator         import itemgetter

def do(StateRouterInfoList):
    """Create code that allows to jump to a state based on an integer value.
    """
    if len(StateRouterInfoList) == 0: return ""
    LanguageDB = Setup.language_db

    txt = [
            "#ifndef QUEX_OPTION_COMPUTED_GOTOS\n",
            "STATE_ROUTER:\n",
            "    switch( target_state_index ) {\n",
    ]

    done_set = set([])
    for index, code in sorted(StateRouterInfoList, key=itemgetter(0)):
        if index in done_set: continue
        done_set.add(index)
        txt.append("    case %i: {" % index)
        txt.append(code)
        txt.append("    }\n")

    txt.append("    }\n")
    txt.append("    __quex_assert(false);\n")
    txt.append("#endif /* QUEX_OPTION_COMPUTED_GOTOS */\n")

    return "".join(txt)

