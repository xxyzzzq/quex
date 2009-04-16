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
    descriptor = TokenTypeDescriptor()

    while parse_section(fh, descriptor):
        pass
        
    if not check(fh, "}"):
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type definition.", fh);

def parse_section(fh, descriptor):
    position = fh.tell()
    skip_whitespace(fh)
    word = read_identifier(fh)

    if word not in ["standard", "distinct", "union"]:
        return False

    if not check(fh, "{"):
        fh.seek(position)
        error_msg("Missing opening '{' at begin of token_type section '%s'." % word, fh);

    if   word == "standard": parse_standard_members(fh, descriptor)
    elif word == "distinct": parse_distinct_members(fh, descriptor)
    elif word == "union":    parse_union_members(fh, descriptor)

    if not check(fh, "}"):
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type section '%s'." % word, fh);

    return True
            
def parse_standard_members(fh, descriptor, already_defined_list):
    position = fh.tell()
    allowed_list = ["column_number", "line_number", "token_id"]

    while 1 + 1 == 2:
        try_position = fh.tell()
        try: 
            type_code_fragment, name = parse_variable_definition(fh) 

        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type header definition.", fh)

        if name == None: return

        __validate_definition(type_code_fragment.filename, type_code_fragment.line_n, name,
                              allowed_list, already_defined_list, NumericF=True)
                              

        if   name == "token_id": descriptor.token_id_type       = type_code_fragment
        elif name == "column":   descriptor.column_counter_type = type_code_fragment
        elif name == "line":     descriptor.line_counter_type   = type_code_fragment
        else:
            assert false # This should have been caught by the variable parser function

        already_defined_list.append([name, type_code_fragment])

def parse_distinct_members(fh, descriptor, already_defined_list):
    position = fh.tell()

    while 1 + 1 == 2:
        try_position = fh.tell()
        try: 
            type_code_fragment, name = parse_variable_definition(fh) 

        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type header definition.", fh)

        if name == None: return

        __validate_definition(type_code_fragment.filename, type_code_fragment.line_n, name,
                              [], already_defined_list, NumericF=True)

        descriptor.distinct_db[name] = type_code_fragment

        already_defined_list.append([name, type_code_fragment])


def parse_union_members(fh, descriptor):
    position = fh.tell()

    while 1 + 1 == 2:
        try_position = fh.tell()
        try: 
            type_code_fragment, name = parse_variable_definition(fh) 

        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type header definition.", fh)

        if name == None: return

        __validate_definition(type_code_fragment.filename, type_code_fragment.line_n, name,
                              [], already_defined_list, NumericF=True)

        descriptor.union_db[name] = type_code_fragment

        already_defined_list.append([name, type_code_fragment])



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
    position = fh.tell()
    type_name       = ""
    array_element_n = -1

    if check(fh, "}"): fh.seek(position); return None, None
    
    line_n = get_current_line_info_number(fh)

    type_str, i = read_until_letter(fh, ":", Verbose=True)
    if i == -1: fh.seek(position); return None, None
    type_str = type_str.strip()

    name_str, i = read_until_letter(fh, ";", Verbose=True)
    if i == -1: error_msg("missing ';'", fh)

    name_str = name_str.strip()

    return UserCodeFragment(type_str, fh.name, line_n), name_str

def __validate_definition(FileName, LineN, TypeStr, NameStr, 
                          AllowedList, DisallowedList, NumericF=False):
    if AllowedList != []:
        if NameStr not in AllowedList:
            error_msg("Name '%s' not allowed in header definition." % NameStr,
                      FileName, LineN)

    if DisallowedList != []:
        DisallowedNameList = map(lambda x: x[0], DisallowedList)
        if NameStr in DisallowedNameList:
            error_msg("Token type member name '%s' defined twice." % NameStr,
                      FileName, LineN, DontExitF=False)
            error_msg("Previously defined here.",
                      x[1].filename, x[1].line_n)
    if NumericF:
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


