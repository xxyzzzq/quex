from quex.frs_py.file_in                    import *
from quex.core_engine.generator.action_info import UserCodeFragment, CodeFragment


class TokenTypeDescriptor:
    def __init__(self):
        self.token_id_type      = CodeFragment("QUEX_TYPE_TOKEN_ID")
        self.column_number_type = CodeFragment("size_t")
        self.line_number_type   = CodeFragment("size_t")
        self.distinct_db = {}
        self.union_db    = {}

    def __repr__(self):
        txt  = "type(token_id)      = %s\n" % self.token_id_type.get_code()
        txt += "type(column_number) = %s\n" % self.column_number_type.get_code()
        txt += "type(line_number)   = %s\n" % self.line_number_type.get_code()

        txt += "distinct members {\n"
        # '0' to make sure, that it works on an empty sequence too.
        L = max([0] + map(lambda x: len(x.get_code()), self.distinct_db.values()))
        for name, type_code in self.distinct_db.items():
            txt += "    %s%s %s\n" % (type_code.get_code(), " " * (L - len(type_code.get_code())), name)
        txt += "}\n"
        txt += "union members {\n"

        # '0' to make sure, that it works on an empty sequence too.
        L = 0
        for name, type_descr in self.union_db.items():
            if type(type_descr) == dict:
                length = 4 + max([0] + map(lambda x: len(x.get_code()), type_descr.values()))
            else:
                length = len(type_descr.get_code())
            if length > L: L = length

        for name, type_descr in self.union_db.items():
            if type(type_descr) == dict:
                txt += "    {\n"
                for sub_name, sub_type in type_descr.items():
                    txt += "        %s%s %s\n" % (sub_type.get_code(), " " * (L - len(sub_type.get_code())-4), sub_name)
                txt += "    }\n"
            else:
                txt += "    %s%s %s\n" % (type_descr.get_code(), " " * (L - len(type_descr.get_code())), name)
        txt += "}\n"

        return txt

TokenType_StandardMemberList = ["column_number", "line_number", "id"]

__data_name_index_counter = -1
def data_name_index_counter_get():
    global __data_name_index_counter
    __data_name_index_counter += 1
    return __data_name_index_counter

def parse(fh):
    descriptor = TokenTypeDescriptor()

    if not check(fh, "{"):
        return None

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
    if word == "":
        fh.seek(position)
        error_msg("Missing token_type section ('standard', 'distinct', or 'union').", fh)

    verify_word_in_list(word, SubsectionList, 
                        "Subsection '%s' not allowed in token_type section." % word, fh)

    if not check(fh, "{"):
        fh.seek(position)
        error_msg("Missing opening '{' at begin of token_type section '%s'." % word, fh);

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
            result = parse_variable_definition(fh) 
        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type 'standard' section.", fh)

        if result == None: return
        type_code_fragment, name = result[0], result[1]

        __validate_definition(type_code_fragment, name,
                              already_defined_list, StandardMembersF=True)

        if   name == "id":            descriptor.token_id_type      = type_code_fragment
        elif name == "column_number": descriptor.column_number_type = type_code_fragment
        elif name == "line_number":   descriptor.line_number_type   = type_code_fragment
        else:
            assert false # This should have been caught by the variable parser function

        already_defined_list.append([name, type_code_fragment])

def parse_distinct_members(fh, descriptor, already_defined_list):
    result = parse_variable_definition_list(fh, "distinct", already_defined_list)
    if result == {}: 
        error_msg("Missing variable definition in token_type 'distinct' section.", fh)
    descriptor.distinct_db = result

def parse_union_members(fh, descriptor, already_defined_list):
    result = parse_variable_definition_list(fh, "union", already_defined_list, 
                                                         GroupF=True)
    if result == {}: 
        error_msg("Missing variable definition in token_type 'union' section.", fh)
    descriptor.union_db = result

def parse_variable_definition_list(fh, SectionName, already_defined_list, GroupF=False):
    position = fh.tell()

    db = {}
    while 1 + 1 == 2:
        try_position = fh.tell()
        try: 
            result = parse_variable_definition(fh, GroupF=True, already_defined_list=already_defined_list) 
        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type '%s' subsection." % SectionName, fh)

        if result == None: return db

        # The type_descriptor can be:
        #  -- a UserCodeFragment with a string of the type
        #  -- a dictionary that contains the combined variable definitions.
        type_descriptor = result[0]

        # If only one argument was returned it was a 'struct' that requires
        # an implicit definition of the struct that combines the variables.
        if len(result) == 1: name = "data_" + repr(data_name_index_counter_get())
        else:                name = result[1]

        db[name] = type_descriptor

        if len(result) == 1:
            assert type(type_descriptor) == dict
            # In case of a 'combined' definition each variable needs to be validated.
            for sub_name, sub_type in type_descriptor.items():
                __validate_definition(sub_type, sub_type, already_defined_list, 
                                      StandardMembersF=False)

                already_defined_list.append([sub_name, sub_type])
        else:
            assert type_descriptor.__class__.__name__ == "UserCodeFragment"
            __validate_definition(type_descriptor, name, already_defined_list, 
                                  StandardMembersF=False)
            already_defined_list.append([name, type_descriptor])

def parse_variable_definition(fh, GroupF=False, already_defined_list=[]):
    """PURPOSE: Parsing of a variable definition consisting of 'type' and 'name.
                Members can be mentioned together in a group, which means that
                they can appear simultaneously. Possible expresions are

                (1) single variables:

                              name0 : type;
                              name1 : type[32];
                              name2 : type*;

                (2) combined variables

                              {
                                  sub_name0 : type0;
                                  sub_name1 : type[64];
                                  sub_name2 : type1*;
                              }

       ARGUMENTS: 

        'GroupF'               allows to have 'nested variable groups' in curly brackets

        'already_defined_list' informs about variable names that have been already
                               chosen. It is only used for groups.

       RETURNS:
                 None        on failure to pass a variable definition.
                 array       when a single variable definition was found. 
                                array[0] = UserCodeFragment containing the type. 
                                array[1] = name of the variable.
                 dictionary  if it was a combined variable definition. The dictionary
                               maps: (variable name) ---> (UserCodeFragment with type)
    
    """
    position = fh.tell()
    type_name       = ""
    array_element_n = -1

    line_n   = get_current_line_info_number(fh)
    skip_whitespace(fh)
    name_str = read_identifier(fh)
    if name_str == "":
        if not GroupF or not check(fh, "{"): 
            fh.seek(position); 
            return None
        sub_db = parse_variable_definition_list(fh, "concurrent union variables", already_defined_list)
        if not check(fh, "}"): 
            fh.seek(position)
            error_msg("Missing closing '}' after concurrent variable definition.", fh)
        return [ sub_db ]

    else:
        name_str = name_str.strip()
        if not check(fh, ":"): error_msg("missing ':' after identifier '%s'." % name_str, fh)

        type_str, i = read_until_letter(fh, ";", Verbose=True)
        if i == -1: error_msg("missing ';'", fh)
        type_str = type_str.strip()

        return [ UserCodeFragment(type_str, fh.name, line_n), name_str ]

def __validate_definition(TypeCodeFragment, NameStr, 
                          AlreadyMentionedList, StandardMembersF):
    FileName = TypeCodeFragment.filename
    LineN    = TypeCodeFragment.line_n
    if StandardMembersF:
        verify_word_in_list(NameStr, TokenType_StandardMemberList, 
                            "Member name '%s' not allowed in token_type section 'standard'." % NameStr, 
                            FileName, LineN)

        # Standard Members are all numeric types
        TypeStr = TypeCodeFragment.get_code()
        if    TypeStr.find("string") != -1 \
           or TypeStr.find("vector") != -1 \
           or TypeStr.find("map")    != -1:
            error_msg("Numeric type required.\n" % Description + \
                      "Example: <token_id: uint16_t>, Found: '%s'\n" % TypeStr, fh)
    else:
        if NameStr in TokenType_StandardMemberList:
            error_msg("Member '%s' only allowed in 'standard' section." % NameStr,
                      FileName, LineN)

    for candidate in AlreadyMentionedList:
        if candidate[0] != NameStr: continue 
        error_msg("Token type member name '%s' defined twice." % NameStr,
                  FileName, LineN, DontExitF=True)
        error_msg("Previously defined here.",
                  candidate[1].filename, candidate[1].line_n)


    
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


