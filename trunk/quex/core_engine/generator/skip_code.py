
def get_character_range_skip_code(EndSequence, LanguageDB, BufferEndLimitCode,
                                  BufferReloadRequiredOnDropOutF=True):
    """Produces a 'range skipper until an ending string occurs. This follows 
       the following scheme:

        do {

            input = get_character();
            if( input != CHAR1 ) { continue; } 
            
            input = get_character();
            if( input != CHAR2 ) { continue; } 
            
            input = get_character();
            if( input != CHAR3 ) { continue; } 
            
            ... 
            input = get_character();
            if( input == CHAR_N ) { goto INITIAL_STATE; /* end of skip range has been found */ } 
             
        } while( input != buffer_limit_code );

    """
    assert EndSequence.__class__  == list
    assert map(type, EndSequence) == [int] * len(EndSequence)

    # Use two endless loops in order to avoid gotos
    msg  = LanguageDB["$loop-start-endless"]
    msg += "    " + LanguageDB["$loop-start-endless"]
    msg += "        " + LanguageDB["$input/get"] + "\n"
    msg += "        " + LanguageDB["$if =="](repr(EndSequence[0]))
    msg += "            " + LanguageDB["$break"]
    msg += "        " + LanguageDB["$endif"]
    msg += "        " + LanguageDB["$if =="](repr(BufferEndLimitCode))
    msg += "        " + LanguageDB["$drop-out"](StateMachineName="<<TestMachine>>", 
                                   CurrentStateIdx=4711, 
                                   BackwardLexingF=False,
                                   BufferReloadRequiredOnDropOutF=BufferReloadRequiredOnDropOutF,
                                   DropOutTargetStateID=4711).replace("\n", "\n        ")
    msg += "        " + LanguageDB["$endif"]
    msg += "    " + LanguageDB["$loop-end"]
    txt  = ""
    for value in EndSequence[1:]:
        # If the last character of the sequence matches than we break out
        sgm  = LanguageDB["$input/get"] + "\n"
        sgm += LanguageDB["$if =="](repr(value))
        sgm += "    " + LanguageDB["$goto-start"]
        sgm += LanguageDB["$endif"]
        txt += "    " + sgm.replace("\n", "\n    ")

    msg += "    " + txt.replace("\n", "\n    ")

    msg += LanguageDB["$loop-end"]


    return msg




