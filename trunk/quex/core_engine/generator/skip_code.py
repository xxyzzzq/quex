
def get_range_skipper(EndSequence, LanguageDB, BufferEndLimitCode,
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
    assert len(EndSequence) >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)

    drop_out_code = LanguageDB["$drop-out-forward"](OnReloadGotoLabel="INIT_STATE")
    drop_out_code = drop_out_code[:-1].replace("\n", "\n        ") + drop_out_code[-1]

    action_on_first_character_match = LanguageDB["$break"]
    if len(EndSequence) == 1:
        action_on_first_character_match = LanguageDB["$goto"]("$re-start")

    # Use two endless loops in order to avoid gotos
    msg  = LanguageDB["$input/get"] + "\n"
    msg += LanguageDB["$loop-start-endless"]
    msg += LanguageDB["$ml-comment"](
            "Most character skipping shall happen by means of a very small piece of code.\n" + \
            "Since most characters are different from the buffer limit code or the range\n"  + \
            "limit, the thread of control will remain mostly inside the small loop.")        + "\n"
    msg += "    " + LanguageDB["$loop-start-endless"]
    msg += "        " + LanguageDB["$if =="](repr(EndSequence[0]))
    msg += "            " + action_on_first_character_match
    msg += "        " + LanguageDB["$endif"]
    msg += "        " + drop_out_code
    msg += "        " + LanguageDB["$input/get"] + "\n"
    msg += "    " + LanguageDB["$loop-end"]
    txt  = ""

    if len(EndSequence) != 1:
        for value in EndSequence[1:-1]:
            # If the last character of the sequence matches than we break out
            sgm  = LanguageDB["$if =="](repr(value))
            sgm += "    " + LanguageDB["$continue"]
            sgm += LanguageDB["$endif"]
            sgm += LanguageDB["$input/get"] + "\n"
            txt += "    " + sgm[:-1].replace("\n", "\n    ") + sgm[-1]

        sgm  = LanguageDB["$if =="](repr(EndSequence[-1]))
        sgm += "    " + LanguageDB["$goto"]("$re-start")
        sgm += LanguageDB["$endif"]
        txt += "    " + sgm[:-1].replace("\n", "\n    ") + sgm[-1]

    msg += txt 
    msg += LanguageDB["$loop-end"]

    return msg



def get_nested_character_skipper(StartSequence, EndSequence, LanguageDB, BufferEndLimitCode,
                                 BufferReloadRequiredOnDropOutF=True):
    assert StartSequence.__class__  == list
    assert len(StartSequence)       >= 1
    assert map(type, StartSequence) == [int] * len(StartSequence)
    assert EndSequence.__class__  == list
    assert len(EndSequence)       >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)
    assert StartSequence != EndSequence

    # Identify the common start of 'StartSequence' and 'EndSequence'
    CommonSequence    = []
    StartSequenceTail = []  # 'un-common' tail of the start sequence
    EndSequenceTail   = []  # 'un-common' tail of the end sequence
    L_min             = min(len(StartSequence), len(EndSequence))
    characters_from_begin_to_i_are_common_f = True
    for i in range(L_min):
        if    (not characters_from_begin_to_i_are_common_f) \
           or (StartSequence[i] != EndSequence[i]): 
            StartSequenceTail.append(StartSequence[i])
            EndSequenceTail.append(EndSequence[i])
             characters_from_begin_to_i_are_common_f = False
        else: 
            CommonSequence.append(StartSequence[i])

    if CommonSequence != []:
        msg += "        " + LanguageDB["$if =="](repr(CommonSequence[0]))
        msg += "            " + action_on_first_character_match
        msg += "        " + LanguageDB["$endif"]
    else:
        msg += "        " + LanguageDB["$if =="](repr(StartSequenceTail[0]))
        msg += "            " + action_on_first_character_match
        msg += "        " + LanguageDB["$endif"]


