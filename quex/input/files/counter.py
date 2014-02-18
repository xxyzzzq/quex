import quex.input.regular_expression.core         as     regular_expression
from   quex.input.files.parser_data.counter       import ParserDataLineColumn, \
                                                         ParserDataIndentation, \
                                                         extract_trigger_set
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.generator.code.base            import LocalizedParameter, SourceRef
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

from   quex.blackboard import setup as Setup

def parse_line_column_counter(fh):
    result = __parse(fh, ParserDataLineColumn(fh))
    return CounterSetupLineColumn(result)

def parse_indentation(fh, IndentationSetupF):
    result = __parse(fh, ParserDataIndentation(fh))
    return CounterSetupIndentation(result)

def __parse_definition_head(fh, result):

    if check(fh, "\\default"): 
        error_msg("'\\default' has been replaced by keyword '\\else' since quex 0.64.9!", fh)
    elif check(fh, "\\else"): 
        pattern = None
    else:                      
        pattern = regular_expression.parse(fh)

    skip_whitespace(fh)
    check_or_die(fh, "=>", " after character set definition.")

    skip_whitespace(fh)
    identifier = read_identifier(fh, OnMissingStr="Missing identifier for indentation element definition.")

    verify_word_in_list(identifier, result.identifier_list, 
                        "Unrecognized specifier '%s'." % identifier, fh)
    skip_whitespace(fh)

    return pattern, identifier

def __parse(fh, result, IndentationSetupF=False):
    """Parses pattern definitions of the form:
   
          [ \t]                                       => grid 4;
          [:intersection([:alpha:], [\X064-\X066]):]  => space 1;

       In other words the right hand side *must* be a character set.
    """

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)

    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, ">"): 
            break
        
        # A regular expression state machine
        pattern, identifier = __parse_definition_head(fh, result)
        if pattern is None and IndentationSetupF:
            error_msg("Keyword '\\else' cannot be used in indentation setup.", fh)

        sr = SourceRef.from_FileHandle(fh)
        # The following treats ALL possible identifiers, including those which may be 
        # inadmissible for a setup. 'verify_word_in_list()' would abort in case that
        # an inadmissible identifier has been found--so there is no harm.
        if identifier == "space":
            value = read_value_specifier(fh, identifier, 1)
            result.specify(identifier, pattern, value, sr)

        elif identifier == "grid":
            value = read_value_specifier(fh, identifier)
            result.check_grid_specification(value, sr)
            result.specify(identifier, pattern, value, sr)

        elif identifier == "bad":
            result.specify(identifier, pattern, -1, sr)

        elif IndentationSetupF:
            if identifier == "newline":
                result.specify_newline(pattern, sr)
            elif identifier == "suppressor":
                result.specify_suppressor(pattern, sr)

        elif identifier == "newline":
            value = read_value_specifier(fh, identifier)
            result.specify(identifier, pattern, value, sr)

        else:
            assert False, "Unreachable code reached."

        if not check(fh, ";"):
            error_msg("Missing ';' after '%s' specification." % identifier, fh)

    # Assig the 'else' command to all the remaining places in the character map.
    if not IndentationSetupF:
        result.count_command_map.assign_else_count_command(0, Setup.get_character_value_limit())

    result.consistency_check(fh)
    return result

def read_value_specifier(fh, Keyword, Default=None):
    skip_whitespace(fh)
    value = read_integer(fh)
    if value is not None:     return value

    # not a number received, is it an identifier?
    variable = read_identifier(fh)
    if   variable != "":      return variable
    elif Default is not None: return Default

    error_msg("Missing integer or variable name after keyword '%s'." % Keyword, fh) 

