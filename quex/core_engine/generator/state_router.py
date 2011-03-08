from quex.input.setup import setup as Setup
from quex.core_engine.generator.languages.address import Address, get_label, get_address
from operator         import itemgetter

def do(StateRouterInfoList):
    """Create code that allows to jump to a state based on an integer value.
    """
    if len(StateRouterInfoList) == 0: return ""
    LanguageDB = Setup.language_db

    prolog = "#   ifndef QUEX_OPTION_COMPUTED_GOTOS\n" \
             "    __quex_assert_no_passage();\n"       \
             "__STATE_ROUTER:\n"

    txt = ["    switch( target_state_index ) {\n" ]

    done_set = set([])
    for index, code in sorted(StateRouterInfoList, key=itemgetter(0)):
        if index in done_set: continue
        done_set.add(index)
        txt.append("        case %i: { " % index)
        if type(code) == list: txt.extend(code)
        else:                  txt.append(code)
        txt.append("}\n")

    txt.append("\n")
    txt.append("        default:\n")
    txt.append("            __QUEX_STD_fprintf(stderr, \"State router: index = %i\\n\", (int)target_state_index);\n")
    txt.append("            QUEX_ERROR_EXIT(\"State router: unknown index.\");\n")
    txt.append("    }\n")

    epilog = "#   endif /* QUEX_OPTION_COMPUTED_GOTOS */\n"

    return [prolog, Address("$state-router", None, txt), epilog]

def get_info(StateIndexList):
    LanguageDB = Setup.language_db

    # Make sure, that for every state the 'drop-out' state is also mentioned
    result = [None] * len(StateIndexList)
    for i, index in enumerate(StateIndexList):
        assert type(index) != str
        if index >= 0:
            # Transition to state entry
            code = "goto " + get_label("$entry", index) + "; "
            result[i] = (index, code)
        else:
            # Transition to a templates 'drop-out'
            code = "goto " + get_label("$drop-out", - index) + "; "
            result[i] = (get_address("$drop-out", - index), code)
    return result
