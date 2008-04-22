from StringIO import StringIO
from   quex.frs_py.file_in          import EndOfStreamException, error_msg
from   quex.exception               import RegularExpressionException
import quex.lexer_mode              as lexer_mode
import quex.core_engine.regular_expression.core as regex
import quex.core_engine.regular_expression.character_set_expression as charset_expression

def parse(fh, Setup):

    start_position = fh.tell()
    try:
        # (*) parse regular expression, build state machine
        pattern_state_machine = regex.do(fh, lexer_mode.shorthand_db, 
                                         BeginOfFile_Code           = Setup.begin_of_stream_code,
                                         EndOfFile_Code             = Setup.end_of_stream_code,
                                         DOS_CarriageReturnNewlineF = not Setup.no_dos_carriage_return_newline_f)

        # (*) error in regular expression?
        if pattern_state_machine == None:
            error_msg("No valid regular expression detected.", fh)

    except RegularExpressionException, x:
        fh.seek(start_position)
        error_msg("Regular expression parsing:\n" + x.message, fh)

    except EndOfStreamException:
        fh.seek(start_position)
        error_msg("End of file reached while parsing regular expression.", fh)

    end_position = fh.tell()

    fh.seek(start_position)
    regular_expression = fh.read(end_position - start_position)

    return regular_expression, pattern_state_machine


def parse_character_set(Txt_or_File):

    if Txt_or_File.__class__ in [file, StringIO]:
        sh       = Txt_or_File
        sh_ref   = sh
        position = sh.tell()
    else:
        sh     = StringIO(Txt_or_File)
        sh_ref = -1

    try:
        # -- parse regular expression, build state machine
        character_set = charset_expression.snap_set_expression(sh)

        if character_set == None:
            error_msg("No valid regular character set expression detected.", sh_ref)

    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message, sh_ref)

    except EndOfStreamException:
        if sh_ref != -1: sh_ref.seek(position)
        error_msg("End of character set expression reached while parsing.", sh_ref)

    return character_set

def parse_character_string(Txt_or_File):

    if Txt_or_File.__class__ in [file, StringIO]:
        sh       = Txt_or_File
        sh_ref   = sh
        position = sh.tell()
    else:
        sh     = StringIO(Txt_or_File)
        sh_ref = -1

    try:
        # -- parse regular expression, build state machine
        state_machine = snap_character_string.do(sh)

        if character_set == None:
            error_msg("No valid regular character string expression detected.", sh_ref)

    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message, sh_ref)

    except EndOfStreamException:
        if sh_ref != -1: sh_ref.seek(position)
        error_msg("End of character string reached while parsing.", sh_ref)

    return state_machine

