
def get_character_range_skip_code(LanguageDB, EndSequence, BufferEndLimitCode):
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
    assert EndSequence.__class__     == list
    assert lambda(type, EndSequence) == [int] * len(EndSequence)

    # Use two endless loops in order to avoid gotos
    txt = LanguageDB["$loop-start-endless"]
    txt = "    " + LanguageDB["$loop-start-endless"]
    for value in EndSequence[:-1]:
        txt += LanguageDB["$input/get"]
        txt += LanguageDB["$if !="](value)
        txt += "    " + LanguageDB["$break"]
        txt += LanguageDB["$endif"]
    # If the last character of the sequence matches than we break out
    txt += LanguageDB["$input/get"]
    txt += LanguageDB["$if =="](value)
    txt += "    " + LanguageDB["$goto-initial-state"]
    txt += LanguageDB["$endif"]

    txt += LanguageDB["$loop-end"]

    txt += LanguageDB["$if =="](repr(BufferEndLimitCode))
    txt += LanguageDB["$drop-out"](StateMachineName, CurrentStateIdx, BackwardLexingF=False,
                                   BufferReloadRequiredOnDropOutF=BufferReloadRequiredOnDropOutF,
                                   DropOutTargetStateID=InitStateIndex)
    txt += LanguageDB["$endif"]
    txt += LanguageDB["$loop-end"]






