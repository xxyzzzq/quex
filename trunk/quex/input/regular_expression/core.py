from StringIO import StringIO
from   quex.blackboard import setup as Setup

from   quex.engine.misc.file_in       import EndOfStreamException, error_msg, error_eof
from   quex.exception                 import RegularExpressionException
from   quex.engine.interval_handling  import NumberSet, Interval
from   quex.engine.state_machine.core import StateMachine 
import quex.blackboard                                        as blackboard
import quex.input.regular_expression.engine                   as regex
from   quex.input.regular_expression.construct                import Pattern
import quex.input.regular_expression.character_set_expression as charset_expression
import quex.input.regular_expression.snap_character_string    as snap_character_string

def parse(Txt_or_File, AllowNothingIsFineF=False, AllowStateMachineTrafoF=True):

    sh, sh_ref, start_position = __prepare_text_or_file_stream(Txt_or_File)

    start_position, pattern_str, pattern = __parse(sh)

    return pattern_str, pattern

def parse_character_string(Txt_or_File):

    start_position, pattern_str, pattern = __parse(sh)

    # Check whether it is a simple sequence.
    character_sequence = pattern.sm.get_number_sequence()
    if    pattern.has_pre_context() or pattern.has_post_context() \
       or character_sequence is None:
        fh.seek(start_position)
        error_msg("Regular expression cannot be interpreted as plain character string.", fh)

    return pattern_str, pattern, character_sequence

def parse_character_set(Txt_or_File):
    start_position, pattern_str, pattern = __parse(sh)

    # Check whether it is a simple character set.
    character_set = pattern.sm.get_number_set()
    if    pattern.has_pre_context() or pattern.has_post_context() \
       or character_set is None:
        fh.seek(start_position)
        error_msg("Regular expression cannot be interpreted as plain character set.", fh)

    return pattern_str, pattern, character_set

def __parse(Txt_or_File, AllowNothingIsFineF=False, AllowStateMachineTrafoF=True):

    start_position = sh.tell()
    try:
        # (*) parse regular expression, build state machine
        pattern = regex.do(sh, blackboard.shorthand_db, 
                           AllowNothingIsNecessaryF = AllowNothingIsFineF,
                           AllowStateMachineTrafoF  = AllowStateMachineTrafoF)

    except RegularExpressionException, x:
        sh.seek(start_position)
        error_msg("Regular expression parsing:\n" + x.message, sh)

    except EndOfStreamException:
        sh.seek(start_position)
        error_eof("regular expression", sh)

    end_position = fh.tell()
    fh.seek(StartPosition)
    pattern_str = fh.read(end_position - StartPosition)
    if pattern_str == "":
        pattern_str = fh.read(1)
        fh.seek(-1, 1)

    return start_position, pattern_str, pattern

def __prepare_text_or_file_stream(Txt_or_File):
    if Txt_or_File.__class__ in [file, StringIO]:
        sh       = Txt_or_File
        sh_ref   = sh
    else:
        sh     = StringIO(Txt_or_File)
        sh_ref = -1

    return sh, sh_ref, sh.tell()

def __post_process(fh, StartPosition, Result, ReturnRE_StringF):
    assert    Result is None                   \
           or isinstance(Result, Pattern) \
           or isinstance(Result, StateMachine) \
           or isinstance(Result, NumberSet)

    if False and isinstance(fh, StringIO):
        regular_expression = "" # Earlier there was some doubt in StringIO ...
    else:
        end_position = fh.tell()
        fh.seek(StartPosition)
        regular_expression = fh.read(end_position - StartPosition)
        if regular_expression == "":
            regular_expression = fh.read(1)
            fh.seek(-1, 1)

    # (*) error in regular expression?
    if Result is None:
        error_msg("No valid regular expression detected, found '%s'." % regular_expression, fh)

    # NOT: Do not transform here, since transformation might happen twice when patterns
    #      are defined and when they are replaced.
    if ReturnRE_StringF: return regular_expression, Result
    else:                return Result


