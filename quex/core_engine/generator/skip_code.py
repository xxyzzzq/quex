import quex.state_machine.index as sm_index
import quex.core_engine.utf8 as utf8

range_skipper_template = """
    const QUEX_CHARACTER_TYPE   $$SKIPPER$$_Delimiter = { $$DELIMITER$$ };
$$SKIPPER$$_RESTART:
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) 
        goto $$SKIPPER$$_DROP_OUT;

$$SKIPPER$$_RESTART_SAFE:
    end_of_content = QuexBuffer_content_back(&me->buffer) + 1;
    *end_of_content = $$SKIPPER$$_Delimiter[0];       /* Overwrite BufferLimitCode (BLC).  */
    while( *QuexBuffer_input_get(&me->buffer) != $$SKIPPER$_Delimiter[0] )
        QuexBuffer_input_p_increment(&me->buffer);    /* Now, BLC cannot occur. See above. */
    *end_of_content = QUEX_SETTING_BUFFER_LIMIT_CODE; /* Reset BLC.                        */

    if( QuexBuffer_tell_memory_adr(&(me->buffer)) == end_of_content ) $$SKIPPER$$_DROP_OUT;

    /* BLC will cause a mismatch, and drop out after RESTART                               */
    $$DELIMITER_CHAIN_TEST$$            
        goto REENTRY_PREPARATION; /* End of range reached. */
    else   
        goto $$SKIPPER$$_RESTART_SAFE;
 
$$SKIPPER$$_DROP_OUT:
   $$RELOAD$$;
   if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) 
       QUEX_ERROR_EXIT("Missing closing delimiter\n");
   $$SKIPPER$$_RESTART_SAFE;
"""

def get_range_skipper(EndSequence, LanguageDB, BufferEndLimitCode,
                      BufferReloadRequiredOnDropOutF=True):
    """Produces a 'range skipper' until an ending string occurs. This follows 
       the following scheme:
    """
    assert EndSequence.__class__  == list
    assert len(EndSequence) >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)

    # drop_out_code = LanguageDB["$drop-out-forward"](OnReloadGotoLabel="INIT_STATE")
    # drop_out_code = drop_out_code[:-1].replace("\n", "\n        ") + drop_out_code[-1]
    index = sm_index.get()
    skipper_str = "SKIPPER_%i" % int(index)

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
    msg += "        " + LanguageDB["$comment"](utf8.map_unicode_to_utf8(EndSequence[0])) + "\n"
    msg += "        " + LanguageDB["$if =="](repr(EndSequence[0])) 
    msg += "            " + action_on_first_character_match
    msg += "        " + LanguageDB["$endif"]
    msg += "        " + "/* drop_out_code */\n"
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
        if (not characters_from_begin_to_i_are_common_f) or (StartSequence[i] != EndSequence[i]): 
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


