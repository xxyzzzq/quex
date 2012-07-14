import quex.input.files.indentation_setup                  as indentation_setup
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
                              mode_option_info_db 

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
        value = __parse_indentation_handler_setup(fh, new_mode)

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
        opener_str, opener_pattern = regular_expression.parse(fh)
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

def __parse_indentation_handler_setup(fh, new_mode):
    value = indentation_setup.parse(fh)

    # Enter 'Newline' and 'Suppressed Newline' as matches into the engine.
    # Similar to skippers, the indentation count is then triggered by the newline.
    # -- Suppressed Newline = Suppressor followed by Newline,
    #    then newline does not trigger indentation counting.
    suppressed_newline_pattern_str = ""
    if value.newline_suppressor_state_machine.get() is not None:
        suppressed_newline_pattern_str = \
              "(" + value.newline_suppressor_state_machine.pattern_string() + ")" \
            + "(" + value.newline_state_machine.pattern_string() + ")"
                                       
        suppressed_newline_sm = \
            sequentialize.do([value.newline_suppressor_state_machine.get(),
                              value.newline_state_machine.get()])
             
        FileName = value.newline_suppressor_state_machine.file_name
        LineN    = value.newline_suppressor_state_machine.line_n
        # Go back to start.
        code = UserCodeFragment("goto %s;" % get_label("$start", U=True), FileName, LineN)

        new_mode.add_match(suppressed_newline_pattern_str, code, 
                           get_pattern_object(suppressed_newline_sm),
                           Comment=E_SpecialPatterns.SUPPRESSED_INDENTATION_NEWLINE)

    # When there is an empty line, then there shall be no indentation count on it.
    # Here comes the trick: 
    #
    #      Let               newline         
    #      be defined as:    newline ([space]* newline])*
    # 
    # This way empty lines are eaten away before the indentation count is activated.

    # -- 'space'
    x0 = StateMachine()
    x0.add_transition(x0.init_state_index, value.indentation_count_character_set(), 
                      AcceptanceF=True)
    # -- '[space]*'
    x1 = repeat.do(x0)
    # -- '[space]* newline'
    x2 = sequentialize.do([x1, value.newline_state_machine.get()])
    # -- '([space]* newline)*'
    x3 = repeat.do(x2)
    # -- 'newline ([space]* newline)*'
    x4 = sequentialize.do([value.newline_state_machine.get(), x3])
    # -- nfa to dfa; hopcroft optimization
    sm = beautifier.do(x4)

    FileName = value.newline_state_machine.file_name
    LineN    = value.newline_state_machine.line_n
    action   = GeneratedCode(indentation_counter.do, FileName, LineN)

    action.data["indentation_setup"] = value

    new_mode.add_match(value.newline_state_machine.pattern_string(), action, 
                       get_pattern_object(sm), 
                       Comment=E_SpecialPatterns.INDENTATION_NEWLINE)

    # Announce the mode to which the setup belongs
    value.set_containing_mode_name(new_mode.name)

    return value

def read_option_start(fh):
    skip_whitespace(fh)

    # (*) base modes 
    if fh.read(1) != "<": 
        ##fh.seek(-1, 1) 
        return None

    skip_whitespace(fh)
    identifier = read_identifier(fh).strip()

    if identifier == "":  error_msg("missing identifer after start of mode option '<'", fh)
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

