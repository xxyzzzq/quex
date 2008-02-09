from   quex.frs_py.file_in          import EndOfStreamException
from   quex.exception               import RegularExpressionException
import quex.lexer_mode              as lexer_mode
import quex.core_engine.regular_expression.core as regex

def parse(fh, Setup):

    start_position = fh.tell()
    try:
        # -- parse regular expression, build state machine
        pattern_state_machine = regex.do(fh, lexer_mode.shorthand_db, 
                                         Setup.begin_of_stream_code, Setup.end_of_stream_code,
                                         DOS_CarriageReturnNewlineF=Setup.dos_carriage_return_newline_f)
    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message, fh)

    except EndOfStreamException:
        fh.seek(start_position)
        error_msg("End of file reached while parsing regular expression.", fh)


    end_position = fh.tell()

    fh.seek(start_position)
    regular_expression = fh.read(end_position - start_position)

    return regular_expression, pattern_state_machine

