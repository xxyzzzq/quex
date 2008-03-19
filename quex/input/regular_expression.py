from StringIO import StringIO
from   quex.frs_py.file_in          import EndOfStreamException, error_msg
from   quex.exception               import RegularExpressionException
import quex.lexer_mode              as lexer_mode
import quex.core_engine.regular_expression.core as regex
import quex.core_engine.regular_expression.character_set_expression as charset_expression

def parse(fh, Setup):

    start_position = fh.tell()
    try:
        # -- parse regular expression, build state machine
        pattern_state_machine = regex.do(fh, lexer_mode.shorthand_db, 
                                         BeginOfFile_Code           = Setup.begin_of_stream_code,
                                         EndOfFile_Code             = Setup.end_of_stream_code,
                                         DOS_CarriageReturnNewlineF = not Setup.no_dos_carriage_return_newline_f)

        if pattern_state_machine == None:
            error_msg("No valid regular expression detected.", fh)

        orphan_state_list = pattern_state_machine.get_orphaned_state_index_list()
        if orphan_state_list != []:
            error_msg("Orphaned state(s) detected in regular expression (optimization lack).\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
                      "Orphan state(s) = " + repr(orphan_state_list)                       + "\n", 
                      fh, DontExitF=True)

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


def parse_character_set(Txt):

    try:
        # -- parse regular expression, build state machine
        character_set = charset_expression.snap_set_expression(StringIO("[:" + Txt + ":]"))

        if character_set == None:
            error_msg("No valid regular character set expression detected.")

    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message)

    except EndOfStreamException:
        error_msg("End of character set expression reached while parsing.")

    return character_set
