import quex.input.files.counter_setup                      as counter_setup
from   quex.input.regular_expression.construct             import Pattern
import quex.input.regular_expression.core                  as regular_expression
import quex.input.regular_expression.snap_character_string as snap_character_string
import quex.engine.state_machine.algorithm.hopcroft_minimization  as hopcroft
import quex.engine.state_machine.algorithm.nfa_to_dfa             as nfa_to_dfa
import quex.engine.state_machine.algorithm.beautifier             as beautifier
import quex.engine.state_machine.sequentialize             as sequentialize
import quex.engine.state_machine.repeat                    as repeat
from   quex.engine.state_machine.core                      import StateMachine
from   quex.engine.generator.languages.address             import get_label
import quex.engine.generator.skipper.character_set         as     skip_character_set
import quex.engine.generator.skipper.range                 as     skip_range
import quex.engine.generator.skipper.nested_range          as     skip_nested_range
import quex.engine.generator.state.indentation_counter     as     indentation_counter
from   quex.engine.misc.file_in                            import error_msg, \
                                                                  get_current_line_info_number, \
                                                                  skip_whitespace, \
                                                                  read_identifier, \
                                                                  verify_word_in_list
from   quex.engine.generator.action_info                   import UserCodeFragment, \
                                                                  GeneratedCode
from   quex.blackboard import E_SpecialPatterns, \
                              mode_option_info_db, \
                              CounterDB

def parse(fh, new_mode):
    identifier = read_option_start(fh)
    if identifier is None: return False

    verify_word_in_list(identifier, mode_option_info_db.keys(),
                        "mode option", fh.name, get_current_line_info_number(fh))

    if identifier == "skip":
        __parse_skip_option(fh, new_mode)
        return True

    elif identifier in ["skip_range", "skip_nested_range"]:
        __parse_range_skipper_option(fh, identifier, new_mode)
        return True
        
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
    new_mode.add_option(identifier, value)

    return True

def get_pattern_object(SM):
    if not SM.is_DFA_compliant(): result = nfa_to_dfa.do(SM)
    else:                         result = SM
    result = hopcroft.do(result, CreateNewStateMachineF=False)
    return Pattern(result, AllowStateMachineTrafoF=True)

def __parse_skip_option(fh, new_mode):
    """A skipper 'eats' characters at the beginning of a pattern that belong to
    a specified set of characters. A useful application is most probably the
    whitespace skipper '[ \t\n]'. The skipper definition allows quex to
    implement a very effective way to skip these regions."""

    pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)
    skip_whitespace(fh)

    if fh.read(1) != ">":
        error_msg("missing closing '>' for mode option '%s'." % identifier, fh)

    if trigger_set.is_empty():
        error_msg("Empty trigger set for skipper." % identifier, fh)

    # TriggerSet skipping is implemented the following way: As soon as one element of the 
    # trigger set appears, the state machine enters the 'trigger set skipper section'.
    # Enter the skipper as if the opener pattern was a normal pattern and the 'skipper' is the action.
    # NOTE: The correspondent CodeFragment for skipping is created in 'implement_skippers(...)'
    pattern_sm = StateMachine()
    pattern_sm.add_transition(pattern_sm.init_state_index, trigger_set, AcceptanceF=True)

    # Skipper code is to be generated later
    action = GeneratedCode(skip_character_set.do, 
                           FileName = fh.name, 
                           LineN    = get_current_line_info_number(fh))
    action.data["character_set"] = trigger_set

    new_mode.add_match(pattern_str, action, get_pattern_object(pattern_sm), 
                       Comment=E_SpecialPatterns.SKIP)

def __parse_range_skipper_option(fh, identifier, new_mode):
    """A non-nesting skipper can contain a full fledged regular expression as opener,
    since it only effects the trigger. Not so the nested range skipper-see below.
    """

    # -- opener
    skip_whitespace(fh)
    if identifier == "skip_nested_range":
        # Nested range state machines only accept 'strings' not state machines
        opener_str, opener_sequence = __parse_string(fh, "Opener pattern for 'skip_nested_range'")
        opener_sm = StateMachine.from_sequence(opener_sequence)
    else:
        opener_str, opener_pattern = regular_expression.parse(fh, CounterDB=CounterDB)
        opener_sm = opener_pattern.sm
        # For 'range skipping' the opener sequence is not needed, only the opener state
        # machine is webbed into the pattern matching state machine.
        opener_sequence       = None

    skip_whitespace(fh)

    # -- closer
    closer_str, closer_sequence = __parse_string(fh, "Closing pattern for 'skip_range' or 'skip_nested_range'")
    skip_whitespace(fh)
    if fh.read(1) != ">":
        error_msg("missing closing '>' for mode option '%s'" % identifier, fh)

    # Skipper code is to be generated later
    generator_function, comment = { 
            "skip_range":        (skip_range.do,        E_SpecialPatterns.SKIP_RANGE),
            "skip_nested_range": (skip_nested_range.do, E_SpecialPatterns.SKIP_NESTED_RANGE),
    }[identifier]
    action = GeneratedCode(generator_function,
                           FileName = fh.name, 
                           LineN    = get_current_line_info_number(fh))

    action.data["opener_sequence"] = opener_sequence
    action.data["closer_sequence"] = closer_sequence
    action.data["mode_name"]       = new_mode.name

    new_mode.add_match(opener_str, action, get_pattern_object(opener_sm), Comment=comment)

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

def __parse_string(fh, Name):
    pos = fh.tell()
    if fh.read(1) != "\"":
        pos = fh.tell()
        msg = fh.read(5)
        fh.seek(pos)
        error_msg("%s can\n" % Name + 
                  "only be a string and must start with a quote like \".\n" +
                  "Found '%s'" % msg, fh)

    sequence = snap_character_string.get_character_code_sequence(fh)
    end_pos  = fh.tell()
    fh.seek(pos)
    msg      = fh.read(end_pos - pos)
    return msg, sequence

