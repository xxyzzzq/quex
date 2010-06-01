from quex.input.setup import setup as Setup

def do(StateIdx, InitStateF, BackwardLexingF):
    # The initial state starts from the character to be read and is an exception.
    # Any other state starts with an increment (forward) or decrement (backward).
    # This is so, since the beginning of the state is considered to be the 
    # transition action (setting the pointer to the next position to be read).
    LanguageDB = Setup.language_db
    if not BackwardLexingF:
        if not InitStateF:
            txt = [        LanguageDB["$label-def"]("$input", StateIdx), "\n",
                   "    ", LanguageDB["$input/increment"], "\n"]
        else:
            txt = []
    else:
        txt = [         LanguageDB["$label-def"]("$input", StateIdx), "\n",
               "    " + LanguageDB["$input/decrement"], "\n"]

    txt.extend(["    ", LanguageDB["$input/get"], "\n"])

    return txt

