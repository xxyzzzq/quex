from quex.input.setup import setup as Setup
from operator         import itemgetter

def do(StateRouterInfoList):
    """Create code that allows to jump to a state based on an integer value.
    """
    if len(StateRouterInfoList) == 0: return ""
    LanguageDB = Setup.language_db

    txt = [
            "#   ifndef QUEX_OPTION_COMPUTED_GOTOS\n",
            "    __quex_assert_no_passage();\n"
            "__STATE_ROUTER:\n",
            "    switch( target_state_index ) {\n",
    ]

    done_set = set([])
    for index, code in sorted(StateRouterInfoList, key=itemgetter(0)):
        if index in done_set: continue
        done_set.add(index)
        txt.append("        case %i: { " % index)
        txt.append(code)
        txt.append("}\n")

    txt.append("\n")
    txt.append("        default:\n")
    txt.append("            __QUEX_STD_fprintf(stderr, \"State router: index = %i\", (int)target_state_index);\n")
    txt.append("            QUEX_ERROR_EXIT(\"State router: unknown index.\");\n")
    txt.append("    }\n")
    txt.append("#   endif /* QUEX_OPTION_COMPUTED_GOTOS */\n")

    return txt

