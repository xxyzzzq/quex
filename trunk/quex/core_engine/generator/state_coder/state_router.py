from quex.setup import setup as Setup
from operator   import itemgetter

def do(StateRouterInfoList):
    """Create code that allows to jump to a state based on an integer value.
    """
    LanguageDB = Setup.language_db

    txt = [
            "#ifndef QUEX_OPTION_COMPUTED_GOTOS\n",
            "STATE_ROUTER:\n",
            "    switch( target_state_index ) {\n",
    ]

    for index, code in sorted(StateRouterInfoList, key=itemgetter(0)):
        txt.append("    case %i: {" % index)
        txt.append(code)
        txt.append("    }\n")

    txt.append("    }\n")
    txt.append("#endif /* QUEX_OPTION_COMPUTED_GOTOS */\n")

    return txt

