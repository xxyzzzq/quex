import quex.input.regular_expression.core         as     regular_expression
from   quex.input.files.parser_data.counter       import ParserDataLineColumn, \
                                                         ParserDataIndentation
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.generator.code.base            import LocalizedParameter
from   quex.engine.interval_handling              import NumberSet
from   quex.engine.state_machine.core             import StateMachine
from   quex.engine.counter                        import CounterSetupIndentation, \
                                                         CounterSetupLineColumn
from   quex.engine.misc.file_in                   import get_current_line_info_number, \
                                                         error_msg, \
                                                         check, \
                                                         check_or_die, \
                                                         skip_whitespace, \
                                                         read_identifier, \
                                                         verify_word_in_list, \
                                                         read_integer


def parse_line_column_counter(fh):
    result, default_column_n_per_char = __parse(fh, ParserDataLineColumn(fh))
    return CounterSetupLineColumn(result, default_column_n_per_char)

def parse_indentation(fh):
    result, default_column_n_per_char = __parse(fh, ParserDataIndentation(fh))
    return CounterSetupIndentation(result)

def __parse_definition_head(fh, result):

    if check(fh, "\\default"): pattern = None
    else:                      pattern = regular_expression.parse(fh)

    skip_whitespace(fh)
    check_or_die(fh, "=>", " after character set definition.")

    skip_whitespace(fh)
    identifier = read_identifier(fh, OnMissingStr="Missing identifier for indentation element definition.")

    verify_word_in_list(identifier, result.identifier_list, 
                        "Unrecognized specifier '%s'." % identifier, fh)
    skip_whitespace(fh)

def __parse(fh, result):
    """Parses pattern definitions of the form:
   
          [ \t]                                       => grid 4;
          [:intersection([:alpha:], [\X064-\X066]):]  => space 1;

       In other words the right hand side *must* be a character set.
    """

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)

    default_column_n_per_char = 1 # Define spacing of remaining characters
    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, ">"): 
            break
        
        # A regular expression state machine
        pattern, identifier = __parse_definition_head(fh, result)
        if pattern is None:
            # The '\\default' only has meaning for 'space' in a counter setup
            if identifier != "space":
                error_msg("Keyword '\\default' can only be used for definition of 'space'.", fh)
            elif IndentationSetupF:
                error_msg("Keyword '\\default' cannot be used in indentation setup.", fh)
            default_column_n_per_char = read_value_specifier(fh, "space", 1)

        else:
            # The following treats ALL possible identifiers, including those which may be 
            # inadmissible for a setup. 'verify_word_in_list()' would abort in case that
            # an inadmissible identifier has been found--so there is no harm.
            if identifier == "space":
                value = read_value_specifier(fh, "space", 1)
                char_set = extract_trigger_set(fh, pattern, "space")
                result.specify_space(char_set, value, fh)

            elif identifier == "grid":
                value = read_value_specifier(fh, "grid")
                char_set = extract_trigger_set(fh, pattern, "grid")
                result.specify_grid(char_set, value, fh)

            elif identifier == "bad":
                char_set = extract_trigger_set(fh, pattern, "bad")
                result.specify_bad(char_set, fh)

            elif identifier == "newline":
                if IndentationSetupF:
                    result.specify_newline(pattern, fh)
                else:
                    value    = read_value_specifier(fh, "newline", 1)
                    char_set = extract_trigger_set(fh, pattern, "newline")
                    result.specify_newline(char_set, value, fh)

            elif identifier == "suppressor":
                result.specify_suppressor(pattern, fh)

            else:
                assert False, "Unreachable code reached."

        if not check(fh, ";"):
            error_msg("Missing ';' after '%s' specification." % identifier, fh)

    result.consistency_check(fh)
    return result, default_column_n_per_char

def read_value_specifier(fh, Keyword, Default=None):
    skip_whitespace(fh)
    value = read_integer(fh)
    if value is not None:     return value

    # not a number received, is it an identifier?
    variable = read_identifier(fh)
    if   variable != "":      return variable
    elif Default is not None: return Default

    error_msg("Missing integer or variable name after keyword '%s'." % Keyword, fh) 

def extract_trigger_set(fh, Keyword, Pattern):
    def check_can_be_matched_by_single_character(SM):
        bad_f      = False
        init_state = SM.get_init_state()
        if SM.get_init_state().is_acceptance(): 
            bad_f = True
        elif len(SM.states) != 2:
            bad_f = True
        # Init state MUST transit to second state. Second state MUST not have any transitions
        elif len(init_state.target_map.get_target_state_index_list()) != 1:
            bad_f = True
        else:
            tmp = set(SM.states.keys())
            tmp.remove(SM.init_state_index)
            other_state_index = tmp.__iter__().next()
            if len(SM.states[other_state_index].target_map.get_target_state_index_list()) != 0:
                bad_f = True

        if bad_f:
            error_msg("For '%s' only patterns are addmissible which\n" % Keyword + \
                      "can be matched by a single character, e.g. \" \" or [a-z].", fh)

    check_can_be_matched_by_single_character(Pattern.sm)

    transition_map = Pattern.sm.get_init_state().target_map.get_map()
    assert len(transition_map) == 1
    return transition_map.values()[0]

