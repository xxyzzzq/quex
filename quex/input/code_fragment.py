from   quex.frs_py.file_in import *
import quex.lexer_mode     as lexer_mode

def parse(fh, code_fragment_name):
    result = lexer_mode.ReferencedCodeFragment()
    
    dummy, i = read_until_letter(fh, ["{"], Verbose=True)

    if i == -1: error_msg("missing open bracket after %s definition." % code_fragment_name, fh)

    result.code = read_until_closing_bracket(fh, "{", "}")
    result.filename = fh.name
    result.line_n   = get_current_line_info_number(fh)

    return result

def parse_unique(fh, code_fragment_name, possible_code_fragment_carrier):
    """Parse a code fragment that can only be defined once. That includes that
       and error is sent, if it is tried to define it a second time.
    """   
    if possible_code_fragment_carrier.line_n != -1:
        error_msg("%s defined twice" % code_fragment_name, fh, DontExitF=True)
        error_msg("previously defined here", 
                  possible_code_fragment_carrier.filename,
                  possible_code_fragment_carrier.line_n)

    result = parse(fh, code_fragment_name)
    # assign values to existing object
    possible_code_fragment_carrier.code     = result.code
    possible_code_fragment_carrier.filename = result.filename
    possible_code_fragment_carrier.line_n   = result.line_n
    
