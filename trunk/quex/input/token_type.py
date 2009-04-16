from   quex.frs_py.file_in          import *
from   quex.core_engine.generator.action_info import UserCodeFragment, CodeFragment


class TokenTypeDescriptor:
    def __init__(self):
        self.token_id_type        = CodeFragment()
        self.column_counter_type  = CodeFragment()
        self.line_counter_type    = CodeFragment()
        self.header_variable_list = []

    def __repr__(self):
        txt  = "type(token_id)       = %s\n" % self.token_id_type.get_code()
        txt += "type(column_counter) = %s\n" % self.column_counter_type.get_code()
        txt += "type(line_counter)   = %s\n" % self.line_counter_type.get_code()
        txt += "header variables {\n"
        # '0' to make sure, that it works on an empty sequence too.
        L = max([0] + map(lambda x: len(x[0].get_code()), self.header_variable_list))
        for type_str, name in self.header_variable_list:
            txt += "    %s%s %s\n" % (type_str.get_code(), " " * (L - len(type_str.get_code())), name)
        txt += "}\n"
        return txt

def parse(fh):
    # NOTE: Catching of EOF happens in caller: parse_section(...), the caller

    option_list = parse_token_type_options(fh)
    #
    dummy, i = read_until_letter(fh, ["{"], Verbose=True)

    while 1 + 1 == 2:
        if check(fh, "{"):
            # Combined token type members (members that can occur at the same time)
            combined_member_list = []
            while 1 + 1 == 2:
                member = parse_token_type_member_definition(fh)
                if member == None: break
                combined_member_list.append(member)
            # Closing '}' has been eaten by parse_token_type_member_definition(..)
            token_type_member_list.append(combined_member_list)
        else:
            member = parse_token_type_member_definition(fh)
            if member == None: break
            token_type_member_list.append([member])
            
def parse_options(fh, descriptor):
    """SYNTAX: <head:  std::string        name>
               <head:  std::vector<int>   number_list>
               <column:   uint32_t>
               <line:     uint32_t>
               <token_id: uint8_t>
    """
    position = fh.tell()
    allowed_list = ["head", "column", "line", "token_id"]

    while 1 + 1 == 2:
        try: 
            type_code_fragment, name = parse_variable_definition(fh, AllowedList=allowed_list)
        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type header definition.", fh)

    if name == None: return

    if name == "head":
        descriptor.header_variable_list.append([type_code_fragment, name])
    elif identifier == "token_id":
        descriptor.token_id_type = type_code_fragment
    elif identifier == "column":
        descriptor.column_counter_type = type_code_fragment
    elif identifier == "line":
        descriptor.line_counter_type = type_code_fragment


def parse_variable_definition(fh, AllowedList=[], DisallowedList=[], AllowCombinedF=False, NumericF=False):
    """SYNTAX:
              type     : member_name ;
              type[32] : member_name ;
              type*    : member_name ;
              combined:
              {
                 [ member_def ]+
              }
    """
    type_name       = ""
    array_element_n = -1

    if check(fh, "}"): return None, None
    
    line_n = get_current_line_info_number(fh)

    type_str, i = read_until_letter(fh, ":", Verbose=True)
    if i == -1: error_msg("token type definition: missing member type identifier.", fh)
    type_str = type_str.strip()

    name_str, i = read_until_letter(fh, ";", Verbose=True)
    if i == -1: error_msg("missing ';'" % type_str, fh)

    name_str = name_str.strip()

    __validate_definition(fh.name, line_n, type_str, name_str, 
                          AllowedList, DisallowedList, NumericF)

    return UserCodeFragment(type_str, fh.name, line_n), name

def __validate_definition(FileName, LineN, TypeStr, NameStr, 
                          AllowedList, DisallowedList, NumericF=False):
    if AllowedList != []:
        if NameStr not in AllowedList:
            error_msg("Name '%s' not allowed in header definition." % NameStr,
                      FileName, LineN)

    elif DisallowedList != []:
        if NameStr in map(lambda x: x[0], DisallowedList):
            error_msg("Token type member name '%s' defined twice." % NameStr,
                      FileName, LineN, DontExitF=False)
            error_msg("Previously defined here.",
                      x[1], x[2])
    elif NumericF:
        if    TypeStr.find("string") != -1 \
           or TypeStr.find("vector") != -1 \
           or TypeStr.find("map")    != -1:
            error_msg("Numeric type required.\n" % Description + \
                      "Example: <token_id: uint16_t>, Found: '%s'\n" % TypeStr, fh)


    
def something_different(fh):
    # -- get the name of the pattern
    skip_whitespace(fh)
    member_name = read_identifier(fh)
    if member_name == "":
        error_msg("Missing identifier for token struct/class member.", fh)

    verify_next_word(fh, ":")

    if check(fh, "}"): 
        error_msg("Missing type for token struct/class member '%s'." % member_name, fh)

    type_name = read_identifier(fh)
    if type_name == "":
        error_msg("Missing type name for token struct/class member.", fh)

    if check(fh, "[") == false:
        skip_whitespace(fh)
        if __check(fh, ";"): 
            error_msg("Missing ';' after token struct/class member '%s' definition." % \
                      member_name, fh)
    else:
        skip_whitespace(fh)
        number_str = read_integer(fh)
        if number_str == "":
            error_msg("Missing integer after '[' in '%s' definition." % member_name, fh)
        array_element_n = int(number_str)

        skip_whitespace(fh)

        if check(fh, "]") == false:
            error_msg("Missing closing ']' in '%s' array definition." % member_name, fh)

        if check(fh, ";"): 
            error_msg("Missing ';' after token struct/class member '%s' definition." % \
                      member_name, fh)

    return TokenTypeMember(member_name, type_name, array_element_n)


