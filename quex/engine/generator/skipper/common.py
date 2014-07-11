import quex.engine.utf8                            as utf8
from   quex.engine.interval_handling               import NumberSet
from   quex.engine.misc.file_in                    import error_msg
from   quex.engine.misc.string_handling            import safe_string
from   quex.blackboard                             import \
                                                          setup as Setup, \
                                                          Lng

__line_counter_in_loop = """
    __QUEX_IF_COUNT_LINES_IF( input == (QUEX_TYPE_CHARACTER)%s ) { 
        __QUEX_IF_COUNT_LINES_ADD((size_t)1);
    }
"""

def line_counter_in_loop():
    TrafoInfo = Setup.buffer_codec_transformation_info
    if TrafoInfo is None: return __line_counter_in_loop % "'\\n'"

    newline_code = get_newline_in_codec(TrafoInfo)
    if newline_code is None: return "" # Codec does not have newline
    else:                    return __line_counter_in_loop % newline_code


__line_column_counter_in_loop = """
    __QUEX_IF_COUNT_IF( input == (QUEX_TYPE_CHARACTER)%s ) { 
        __QUEX_IF_COUNT_LINES_ADD((size_t)1);
        __QUEX_IF_COUNT_COLUMNS_SET((size_t)0);
        __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));
    }
"""

def line_column_counter_in_loop():
    TrafoInfo = Setup.buffer_codec_transformation_info
    if TrafoInfo is None: return __line_column_counter_in_loop % "'\\n'"

    newline_code = get_newline_in_codec(TrafoInfo)
    if newline_code is None: return "" # Codec does not have newline
    else:                    return __line_column_counter_in_loop % newline_code

def get_newline_in_codec(TrafoInfo):
    """Translate the code for the newline character into the given codec by 'TrafoInfo'.

       RETURNS: None if the transformation is not possible.
    """
    tmp = NumberSet(ord('\n'))
    if isinstance(TrafoInfo, (str, unicode)):
        if   TrafoInfo == "utf8-state-split":  pass
        elif TrafoInfo == "utf16-state-split": pass
        else:                                  
            error_msg("Character encoding '%s' unknown to skipper.\n" % TrafoInfo + \
                      "For line number counting assume code of newline character code to be '0x%02X'." % ord('\n'),
                      DontExitF=True)
        return ord('\n')

    tmp.transform(TrafoInfo)
    return tmp.get_the_only_element() # Returns 'None' if there is none

def get_on_skip_range_open(OnSkipRangeOpen, CloserPattern, NestedF=False):
    if len(OnSkipRangeOpen.get_code()) == 0:
        return "%s\n" % Lng.PURE_RETURN

    txt_entry = Lng.DEFINE("Delimiter", 
                           '"%s"' % safe_string(CloserPattern.pattern_string()))
    txt_exit  = Lng.UNDEFINE("Delimiter")
    if NestedF:
        txt_entry += Lng.DEFINE("Counter", 'counter')
        txt_exit  += Lng.UNDEFINE("Counter")
    else:
        txt_entry += Lng.DEFINE("Counter", '0')
        txt_exit  += Lng.UNDEFINE("Counter")

    return "%s/**/%s%s\n/**/%s" % (
        txt_entry,
        Lng.SOURCE_REFERENCED(OnSkipRangeOpen, PrettyF=True),
        Lng.PURE_RETURN,
        txt_exit
    )

def get_character_sequence(Sequence):
    txt         = ""
    comment_txt = ""
    for letter in Sequence:
        comment_txt += "%s, " % utf8.unicode_to_pretty_utf8(letter)
        txt += "0x%X, " % letter

    return txt, comment_txt


