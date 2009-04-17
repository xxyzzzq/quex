from quex.frs_py.file_in                    import *
from quex.core_engine.generator.action_info import UserCodeFragment, CodeFragment


class TokenTypeDescriptor:
    def __init__(self):
        self.token_id_type        = CodeFragment()
        self.column_number_type   = CodeFragment()
        self.line_number_type     = CodeFragment()
        self.distinct_db = {}
        self.union_db    = {}

    def __repr__(self):
        txt  = "type(token_id)      = %s\n" % self.token_id_type.get_code()
        txt += "type(column_number) = %s\n" % self.column_number_type.get_code()
        txt += "type(line_number)   = %s\n" % self.line_number_type.get_code()

        txt += "distinct members {\n"
        distinct_type_list = map(lambda x: x.get_code(), self.distinct_db.values())
        # '0' to make sure, that it works on an empty sequence too.
        L = max([0] + map(lambda x: len(x[0].get_code()), distinct_type_list))
        for name, type_code in self.distinct_db.items():
            txt += "    %s%s %s\n" % (type_code.get_code(), " " * (L - len(type_code.get_code())), name)
        txt += "}\n"
        txt += "union members {\n"

        union_type_list = map(lambda x: x.get_code(), self.union_db.values())
        # '0' to make sure, that it works on an empty sequence too.
        L = max([0] + map(lambda x: len(x[0].get_code()), union_type_list))
        for name, type_code in self.union_db.items():
            txt += "    %s%s %s\n" % (type_code.get_code(), " " * (L - len(type_code.get_code())), name)
        txt += "}\n"

        return txt

TokenType_StandardMemberList = ["column_number", "line_number", "id"]

def parse(fh):
    descriptor = TokenTypeDescriptor()

    while parse_section(fh, descriptor):
        pass
        
    if not check(fh, "}"):
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type definition.", fh);

def parse_section(fh, descriptor, already_defined_list):
    assert type(already_defined_list) == list

    SubsectionList = ["standard", "distinct", "union"]

    position = fh.tell()
    skip_whitespace(fh)
    word = read_identifier(fh)

    if word not in SubsectionList:
        return False

    if not check(fh, "{"):
        fh.seek(position)
        error_msg("Missing opening '{' at begin of token_type section '%s'." % word, fh);

    verify_word_in_list(word, SubsectionList, 
                        "Subsection '%s' not allowed in token_type section." % word, fh)

    if   word == "standard": parse_standard_members(fh, descriptor, already_defined_list)
    elif word == "distinct": parse_distinct_members(fh, descriptor, already_defined_list)
    elif word == "union":    parse_union_members(fh, descriptor, already_defined_list)

    if not check(fh, "}"):
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type section '%s'." % word, fh);

    return True
            
def parse_standard_members(fh, descriptor, already_defined_list):
    position = fh.tell()

    while 1 + 1 == 2:
        try_position = fh.tell()
        try: 
            type_code_fragment, name = parse_variable_definition(fh) 

        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type 'standard' section.", fh)

        if name == None: return

        __validate_definition(type_code_fragment, name,
                              already_defined_list, StandardMembersF=True)

        if   name == "id":            descriptor.token_id_type      = type_code_fragment
        elif name == "column_number": descriptor.column_number_type = type_code_fragment
        elif name == "line_number":   descriptor.line_number_type   = type_code_fragment
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
            error_msg("End of file reached while parsing token_type 'distinct' section.", fh)

        if name == None: return

        __validate_definition(type_code_fragment, name,
                              already_defined_list, StandardMembersF=False)

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
            error_msg("End of file reached while parsing token_type 'union' subsection.", fh)

        if name == None: return

        __validate_definition(type_code_fragment, name, already_defined_list, 
                              StandardMembersF=False)

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

def __validate_definition(TypeCodeFragment, NameStr, 
                          AlreadyMentionedList, StandardMembersF):
    FileName = TypeCodeFragment.filename
    LineN    = TypeCodeFragment.line_n
    if StandardMembersF:
        verify_word_in_list(NameStr, TokenType_StandardMemberList, 
                            "token_type section 'standard'", FileName, LineN)

        # Standard Members are all numeric types
        TypeStr = TypeCodeFragment.get_code()
        if    TypeStr.find("string") != -1 \
           or TypeStr.find("vector") != -1 \
           or TypeStr.find("map")    != -1:
            error_msg("Numeric type required.\n" % Description + \
                      "Example: <token_id: uint16_t>, Found: '%s'\n" % TypeStr, fh)
    else:
        if NameStr in TokenType_StandardMemberList:
            error_msg("Name '%s' only allowed in 'standard' section." % NameStr,
                      FileName, LineN)

    name_list = map(lambda x: x[0], AlreadyMentionedList)
    if NameStr in name_list:
        error_msg("Token type member name '%s' defined twice." % NameStr,
                  FileName, LineN, DontExitF=False)
        error_msg("Previously defined here.",
                  x[1].filename, x[1].line_n)


    
def something_different(fh):
    # -- get the name of the pattern
    skip_whitespace(fh)
    member_name = read_identifier(fh)
    if member_name == None:
        error_msg("Missing identifier for token struct/class member.", fh)

    verify_next_word(fh, ":")

    if check(fh, "}"): 
        error_msg("Missing type for token struct/class member '%s'." % member_name, fh)

    type_name = read_identifier(fh)
    if type_name == None:
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


