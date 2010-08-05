from   quex.frs_py.file_in              import *
from   quex.output.cpp.token_id_maker   import TokenInfo
from   quex.exception                   import RegularExpressionException
import quex.lexer_mode                as lexer_mode
import quex.input.regular_expression  as regular_expression
import quex.input.code_fragment       as code_fragment
from   quex.core_engine.generator.action_info                    import CodeFragment
from   quex.core_engine.generator.state_coder.skipper_core       import create_skip_code, create_skip_range_code
import quex.core_engine.state_machine.index                      as index
from   quex.core_engine.state_machine.core                       import StateMachine
import quex.core_engine.regular_expression.snap_character_string as snap_character_string
from   quex.input.setup                                          import setup as Setup

def parse(fh):
    # NOTE: Catching of EOF happens in caller: parse_section(...)

    skip_whitespace(fh)
    mode_name = read_identifier(fh)
    if mode_name == "":
        error_msg("missing identifier at beginning of mode definition.", fh)

    # NOTE: constructor does register this mode in the mode_db
    new_mode  = lexer_mode.ModeDescription(mode_name, fh.name, get_current_line_info_number(fh))

    # (*) inherited modes / options
    skip_whitespace(fh)
    dummy = fh.read(1)
    if dummy not in [":", "{"]:
        error_msg("missing ':' or '{' after mode '%s'" % mode_name, fh)

    if dummy == ":":
        parse_mode_option_list(new_mode, fh)

    # (*) read in pattern-action pairs and events
    while parse_mode_element(new_mode, fh): 
        pass

    # (*) check for modes w/o pattern definitions
    if not new_mode.has_event_handler() and not new_mode.has_own_matches():
        if new_mode.options["inheritable"] != "only":
            new_mode.options["inheritable"] = "only"
            error_msg("Mode without pattern and event handlers needs to be 'inheritable only'.\n" + \
                      "<inheritable: only> has been added automatically.", fh,  DontExitF=True)

def parse_mode_option_list(new_mode, fh):
    position = fh.tell()
    try:  
        # ':' => inherited modes/options follow
        skip_whitespace(fh)

        # (*) base modes 
        base_modes, i = read_until_letter(fh, ["{", "<"], Verbose=1)
        new_mode.base_modes = split(base_modes)

        if i != 1: return
        fh.seek(-1, 1)

        # (*) options
        while parse_mode_option(fh, new_mode):
            pass

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing options of mode '%s'." % mode_name, fh)

def parse_mode_option(fh, new_mode):

    identifier = read_option_start(fh)
    if identifier == None: return False

    mode_option_name_list = ["skip", "skip_range", "skip_nesting_range" ] + \
                            lexer_mode.mode_option_info_db.keys()
    verify_word_in_list(identifier, mode_option_name_list,
                        "mode option", fh.name, get_current_line_info_number(fh))

    if identifier == "skip":
        # A skipper 'eats' characters at the beginning of a pattern that belong
        # to a specified set of characters. A useful application is most probably
        # the whitespace skipper '[ \t\n]'. The skipper definition allows quex to
        # implement a very effective way to skip these regions.
        pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)
        skip_whitespace(fh)

        if fh.read(1) != ">":
            error_msg("missing closing '>' for mode option '%s'." % identifier, fh)

        if trigger_set.is_empty():
            error_msg("Empty trigger set for skipper." % identifier, fh)

        # TriggerSet skipping is implemented the following way: As soon as one element of the 
        # trigger set appears, the state machine enters the 'trigger set skipper section'.
        opener_sm = StateMachine()
        opener_sm.add_transition(opener_sm.init_state_index, trigger_set, AcceptanceF=True)
            
        # Enter the skipper as if the opener pattern was a normal pattern and the 'skipper' is the action.
        # NOTE: The correspondent CodeFragment for skipping is created in 'implement_skippers(...)'
        new_mode.add_match(pattern_str, CodeFragment(""), opener_sm)

        # The pattern_str will be used as key later to find the related action.
        # It may appear in multiple modes due to inheritance.
        value = [pattern_str, trigger_set]

    elif identifier == "skip_range":
        # A non-nesting skipper can contain a full fledged regular expression as opener,
        # since it only effects the trigger. Not so the nested range skipper-see below.

        # -- opener
        skip_whitespace(fh)
        opener_str, opener_sm = regular_expression.parse(fh)
        skip_whitespace(fh)

        # -- closer
        if fh.read(1) != "\"":
            error_msg("closing pattern for skip_range can only be a string and must start with a quote like \".", fh)
        closer_sequence = snap_character_string.get_character_code_sequence(fh)
        skip_whitespace(fh)
        if fh.read(1) != ">":
            error_msg("missing closing '>' for mode option '%s'" % identifier, fh)

        # Enter the skipper as if the opener pattern was a normal pattern and the 'skipper' is the action.
        # NOTE: The correspondent CodeFragment for skipping is created in 'implement_skippers(...)'
        new_mode.add_match(opener_str, CodeFragment(""), opener_sm)

        # The opener_str will be used as key later to find the related action.
        # It may appear in multiple modes due to inheritance.
        value = [opener_str, closer_sequence]
        
    elif identifier == "skip_nesting_range":
        error_msg("skip_nesting_range is not yet supported.", fh)

    else:
        value = read_option_value(fh)

    # The 'verify_word_in_list()' call must have ensured that the following holds
    assert lexer_mode.mode_option_info_db.has_key(identifier)

    # Is the option of the appropriate value?
    option_info = lexer_mode.mode_option_info_db[identifier]
    if option_info.type != "list" and value not in option_info.domain:
        error_msg("Tried to set value '%s' for option '%s'. " % (Value, Option) + \
                  "Though, possible \n" + \
                  "for this option are %s" % repr(oi.domain), fh)

    # Finally, set the option
    new_mode.add_option(identifier, value)

    return True

def parse_mode_element(new_mode, fh):
    """Returns: False, if a closing '}' has been found.
                True, else.
    """
    position = fh.tell()
    try:
        description = "Pattern or event handler name.\n" + \
                      "Missing closing '}' for end of mode"

        skip_whitespace(fh)
        # NOTE: Do not use 'read_word' since we need to continue directly after
        #       whitespace, if a regular expression is to be parsed.
        position = fh.tell()

        word = read_until_whitespace(fh)
        if word == "}": return False

        # -- check for 'on_entry', 'on_exit', ...
        if check_for_event_specification(word, fh, new_mode): return True

        fh.seek(position)
        description = "Start of mode element: regular expression"
        pattern, pattern_state_machine = regular_expression.parse(fh)

        if new_mode.has_pattern(pattern):
            previous = new_mode.get_pattern_action_pair(pattern)
            error_msg("Pattern has been defined twice.", fh, DontExitF=True)
            error_msg("First defined here.", 
                     previous.action().filename, previous.action().line_n)


        position    = fh.tell()
        description = "Start of mode element: code fragment for '%s'" % pattern

        parse_action_code(new_mode, fh, pattern, pattern_state_machine)

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing %s." % description, fh)

    return True

def parse_action_code(new_mode, fh, pattern, pattern_state_machine):

    position = fh.tell()
    try:
        skip_whitespace(fh)
        position = fh.tell()
            
        code_obj = code_fragment.parse(fh, "regular expression", ErrorOnFailureF=False) 
        if code_obj != None:
            new_mode.add_match(pattern, code_obj, pattern_state_machine)
            return

        fh.seek(position)
        word = read_until_letter(fh, [";"])
        if word == "PRIORITY-MARK":
            # This mark 'lowers' the priority of a pattern to the priority of the current
            # pattern index (important for inherited patterns, that have higher precedence).
            # The parser already constructed a state machine for the pattern that is to
            # be assigned a new priority. Since, this machine is not used, let us just
            # use its id.
            fh.seek(-1, 1)
            check_or_quit(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_priority(pattern, pattern_state_machine, pattern_state_machine.get_id(), 
                                        fh.name, get_current_line_info_number(fh))

        elif word == "DELETION":
            # This mark deletes any pattern that was inherited with the same 'name'
            fh.seek(-1, 1)
            check_or_quit(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_deletion(pattern, pattern_state_machine, fh.name, get_current_line_info_number(fh))
            
        else:
            error_msg("Missing token '{', 'PRIORITY-MARK', 'DELETION', or '=>' after '%s'.\n" % pattern + \
                      "found: '%s'. Note, that since quex version 0.33.5 it is required to add a ';'\n" % word + \
                      "to the commands PRIORITY-MARK and DELETION.", fh)


    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing action code for pattern.", fh)

def check_for_event_specification(word, fh, new_mode):
    pos = fh.tell()

    # Allow '<<EOF>>' and '<<FAIL>>' out of respect for classical tools like 'lex'
    if   word == "<<EOF>>":                  word = "on_end_of_stream"
    elif word == "<<FAIL>>":                 word = "on_failure"
    elif len(word) < 3 or word[:3] != "on_": return False

    comment = "Unknown event handler '%s'. \n" % word + \
              "Note, that any pattern starting with 'on_' is considered an event handler.\n" + \
              "use double quotes to bracket patterns that start with 'on_'."

    verify_word_in_list(word, lexer_mode.event_handler_db.keys(), comment, fh)

    continue_f = True
    if word == "on_end_of_stream":
        # NOTE: The 'ContinueF' is turned of in this case, because when a termination
        #       token is sent, no other token shall follow. Thus, we enforce the
        #       return from the analyzer. Do not allow CONTINUE.
        continue_f = False

    if     word in ["on_entry", "on_exit", "on_indent", "on_dedent"] \
       and Setup.token_policy not in ["queue"] \
       and not Setup.warning_disabled_no_token_queue_f:
        fh.seek(pos)
        error_msg("Using '%s' event handler, while the token queue is disabled.\n" % word + \
                  "Use '--token-policy queue', so then tokens can be sent safer\n" + \
                  "from inside this event handler. Disable this warning by command\n"
                  "line option '--no-warning-on-no-token-queue'.", fh, DontExitF=True) 

    new_mode.events[word] = code_fragment.parse(fh, "%s::%s event handler" % (new_mode.name, word),
                                                ContinueF=continue_f)

    if word == "on_indentation":
        fh.seek(pos)
        error_msg("Definition of 'on_indentation' is no longer supported since version 0.51.1.\n"
                  "Please, use 'on_indent' for the event of an opening indentation and 'on_dedent'\n"
                  "for the event of a closing indentation.", fh, 

    return True

