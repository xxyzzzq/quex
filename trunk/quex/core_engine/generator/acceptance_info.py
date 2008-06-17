from quex.core_engine.generator.languages.core import __nice

def do(state, LanguageDB, BackwardLexingF, BackwardInputPositionDetectionF=False):
    """Two cases:
       -- an origin marks an acceptance state without any post-condition:
          store input position and mark last acceptance state as the state machine of 
          the origin (note: this origin may result through a priorization)
       -- an origin marks an acceptance of an expression that has a post-condition.
          store the input position in a dedicated input position holder for the 
          origins state machine.
    """
    if BackwardInputPositionDetectionF: assert BackwardLexingF

    OriginList = state.origins().get_list()

    if BackwardLexingF:
        # (*) Backward Lexing 
        if not BackwardInputPositionDetectionF:
            return backward_lexing(OriginList, LanguageDB)
        else:
            return backward_lexing_find_core_pattern(OriginList, LanguageDB)
    else:
        # (*) Forward Lexing 
        return forward_lexing(OriginList, LanguageDB)

def backward_lexing(OriginList, LanguageDB):
    """Backward Lexing:
       -- Using an inverse state machine from 'real' current start position backwards
          until a drop out occurs.
       -- During backward lexing, there is no 'winner' so all origins that indicate
          acceptance need to be considered. They raise there flag 'pre-condition fulfilled'.
    """
    assert type(OriginList) == list
    # There should be nothing, but unconditional acceptances or no-acceptance 
    # origins in the list of origins.
    inadmissible_origin_list = filter(lambda origin:
                                      origin.pre_context_begin_of_line_f() or
                                      origin.pre_context_id() != -1L or
                                      origin.post_context_id() != -1L,
                                      OriginList)
    assert inadmissible_origin_list == [], \
           "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________

    ## txt = LanguageDB["$comment"](" origins = %s" % repr(OriginList)) + "\n"
    #
    txt = ""
    for origin in OriginList:
        if origin.store_input_position_f():
            txt += "    " + LanguageDB["$assignment"]("pre_context_%s_fulfilled_f" % __nice(origin.state_machine_id), 1)
    txt += "\n"    

    return txt

def backward_lexing_find_core_pattern(OriginList, LanguageDB):
    """Backward Lexing:
       -- (see above)
       -- for the search of the end of the core pattern, the acceptance position
          backwards must be stored. 
       -- There is only one pattern involved, so no determination of 'who won'
          is important.
    """
    # There should be nothing, but unconditional acceptances or no-acceptance 
    # origins in the list of origins.
    inadmissible_origin_list = filter(lambda origin:
                                      origin.pre_context_begin_of_line_f() or
                                      origin.pre_context_id() != -1L or
                                      origin.post_context_id() != -1L,
                                      OriginList)
    assert inadmissible_origin_list == [], \
           "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________

    for origin in OriginList:
        if origin.store_input_position_f():
            return "    " + LanguageDB["$input/tell_position"]("end_of_core_pattern_position") + "\n"
    return ""

def forward_lexing(OriginList, LanguageDB):

    txt = ""
    # -- get the pattern ids that indicate the start of a post-condition
    #    (i.e. the end of a core pattern where a post condition is to follow).
    # -- collect patterns that reach acceptance at this state.
    final_acceptance_origin_list = []
    for origin in OriginList: 
        if origin.is_end_of_post_contexted_core_pattern():
            assert origin.is_acceptance() == False
            # store current input position, to be restored when post condition really matches
            txt += "    " + LanguageDB["$input/tell_position"](
                             "last_acceptance_%s_input_position" % __nice(origin.state_machine_id)) + "\n"
        elif origin.is_acceptance():
            final_acceptance_origin_list.append(origin)
   
    def __on_detection_code(Origin):
        """Store the name of the winner pattern (last_acceptance) and the position
           where it has matched (use of $input/tell_position).
        """
        assert Origin.is_acceptance()
        info = LanguageDB["$set-last_acceptance"](__nice(Origin.state_machine_id))
        # NOTE: When post conditioned patterns end they do not store the input position.
        #       Rather, the acceptance position of the core pattern is considered.
        if Origin.post_context_id() == -1:
             info += LanguageDB["$input/tell_position"]("last_acceptance_input_position") + "\n"

        return info

    txt += get_acceptance_detector(final_acceptance_origin_list, 
                                   __on_detection_code,
                                   LanguageDB)

    return txt

def get_acceptance_detector(OriginList, get_on_detection_code_fragment, 
                            LanguageDB, StateMachineName=""):
        
    def indent_this(Fragment):
        # do not replace the last '\n' with '\n    '
        return "    " + Fragment[:-1].replace("\n", "\n    ") + Fragment[-1]

    txt = ""
    first_if_statement_f = True
    OriginList.sort()
    for origin in OriginList:
        if not origin.is_acceptance(): continue

        info = get_on_detection_code_fragment(origin)

        if origin.pre_context_id() != -1L:
            if first_if_statement_f: txt += LanguageDB["$if pre-context"](origin.pre_context_id())
            else:                    txt += LanguageDB["$elseif pre-context"](origin.pre_context_id())
            txt += indent_this(info)
            txt += LanguageDB["$endif"]
        
        elif origin.pre_context_begin_of_line_f():
            if first_if_statement_f: txt += LanguageDB["$if begin-of-line"]
            else:                    txt += LanguageDB["$elseif begin-of-line"]
            txt += indent_this(info)
            txt += LanguageDB["$endif"] 
        
        else:
            if first_if_statement_f: 
                txt += info
            else:
                # if an 'if' statements preceeded, the acceptance needs to appear in an else block
                txt += LanguageDB["$else"] + "\n"; 
                txt += indent_this(info)
                txt += LanguageDB["$endif"]

            break  # no need for further pre-condition consideration

        first_if_statement_f = False

    # (*) write code for the unconditional acceptance states
    if txt == "": return ""
    else:         return "    " + txt[:-1].replace("\n", "\n    ") + txt[-1]
