import quex.input.files.counter_setup     as counter_setup
import quex.input.regular_expression.core as regular_expression
from   quex.engine.misc.file_in           import error_msg, \
                                                 get_current_line_info_number, \
                                                 skip_whitespace, \
                                                 read_identifier, \
                                                 verify_word_in_list
from   quex.engine.misc.file_in           import EndOfStreamException
from   quex.blackboard import mode_option_info_db

def parse(fh, new_mode):
    source_reference = SourceRef.from_FileHandle(fh)

    identifier = read_option_start(fh)
    if identifier is None: return False

    verify_word_in_list(identifier, mode_option_info_db.keys(),
                        "mode option", fh.name, get_current_line_info_number(fh))

    if   identifier == "skip":
        value = __parse_skip_option(fh, new_mode, identifier)

    elif identifier in ["skip_range", "skip_nested_range"]:
        value = __parse_range_skipper_option(fh, identifier, new_mode)
        
    elif identifier == "indentation":
        value = counter_setup.parse(fh, IndentationSetupF=True)
        value.set_containing_mode_name(new_mode.name)

    elif identifier == "counter":
        value = counter_setup.parse(fh, IndentationSetupF=False)

    else:
        value = read_option_value(fh)

    # The 'verify_word_in_list()' call must have ensured that the following holds
    assert mode_option_info_db.has_key(identifier)

    # Is the option of the appropriate value?
    option_info = mode_option_info_db[identifier]

    if option_info.domain is not None and value not in option_info.domain:
        error_msg("Tried to set value '%s' for option '%s'. " % (value, identifier) + \
                  "Though, possible for this option are only: %s." % repr(option_info.domain)[1:-1], fh)

    # Finally, set the option
    new_mode.add_option(identifier, value, source_reference)

    return True

def __parse_skip_option(fh, new_mode, identifier):
    """A skipper 'eats' characters at the beginning of a pattern that belong to
    a specified set of characters. A useful application is most probably the
    whitespace skipper '[ \t\n]'. The skipper definition allows quex to
    implement a very effective way to skip these regions."""

    pattern_str, pattern, trigger_set = regular_expression.parse_character_set(fh, ">")

    skip_whitespace(fh)

    if fh.read(1) != ">":
        error_msg("missing closing '>' for mode option '%s'." % identifier, fh)
    elif trigger_set.is_empty():
        error_msg("Empty trigger set for skipper." % identifier, fh)

    return pattern, trigger_set

def __parse_range_skipper_option(fh, identifier, new_mode):
    """A non-nesting skipper can contain a full fledged regular expression as opener,
    since it only effects the trigger. Not so the nested range skipper-see below.
    """

    # Range state machines only accept 'strings' not state machines
    skip_whitespace(fh)
    opener_str, opener_pattern, opener_sequence = regular_expression.parse_character_string(fh, ">")
    skip_whitespace(fh)
    closer_str, closer_pattern, closer_sequence = regular_expression.parse_character_string(fh, ">")

    # -- closer
    skip_whitespace(fh)
    if fh.read(1) != ">":
        error_msg("missing closing '>' for mode option '%s'" % identifier, fh)
    elif len(opener_sequence) == 0:
        error_msg("Empty sequence for opening delimiter.", fh)
    elif len(closer_sequence) == 0:
        error_msg("Empty sequence for closing delimiter.", fh)

    return (opener_str, opener_pattern, opener_sequence, \
            closer_str, closer_pattern, closer_sequence)

def read_option_start(fh):
    skip_whitespace(fh)

    # (*) base modes 
    if fh.read(1) != "<": 
        ##fh.seek(-1, 1) 
        return None

    skip_whitespace(fh)
    identifier = read_identifier(fh, OnMissingStr="Missing identifer after start of mode option '<'").strip()

    skip_whitespace(fh)
    if fh.read(1) != ":": error_msg("missing ':' after option name '%s'" % identifier, fh)
    skip_whitespace(fh)

    return identifier

def read_option_value(fh):

    position = fh.tell()

    value = ""
    depth = 1
    while 1 + 1 == 2:
        try: 
            letter = fh.read(1)
        except EndOfStreamException:
            fh.seek(position)
            error_msg("missing closing '>' for mode option.", fh)

        if letter == "<": 
            depth += 1
        if letter == ">": 
            depth -= 1
            if depth == 0: break
        value += letter

    return value.strip()

