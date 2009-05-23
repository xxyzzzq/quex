from quex.frs_py.file_in                    import *
from quex.core_engine.generator.action_info import UserCodeFragment, CodeFragment
from quex.input.code_fragment import __parse_normal as parse_normal_code_fragment


class TokenTypeDescriptorCore:
    """Object used during the generation of the TokenTypeDescriptor."""
    def __init__(self, Core=None):
        if Core == None:
            self._file_name            = ""
            self.class_name            = "Token"
            self.open_for_derivation_f = False
            self.name_space            = ["quex"]
            self.token_id_type      = CodeFragment("size_t")
            self.column_number_type = CodeFragment("size_t")
            self.line_number_type   = CodeFragment("size_t")
            self.constructor        = CodeFragment("")
            self.copy               = CodeFragment("")
            self.destructor         = CodeFragment("")
            self.body               = CodeFragment("")
            self.distinct_db = {}
            self.union_db    = {}
        else:
            self._file_name            = Core._file_name
            self.class_name            = Core.class_name
            self.open_for_derivation_f = Core.open_for_derivation_f
            self.name_space            = Core.name_space
            self.token_id_type         = Core.token_id_type
            self.column_number_type    = Core.column_number_type
            self.line_number_type      = Core.line_number_type
            self.constructor           = Core.constructor
            self.copy                  = Core.copy
            self.destructor            = Core.destructor
            self.body                  = Core.body
            self.distinct_db           = Core.distinct_db
            self.union_db              = Core.union_db

    def set_file_name(self, FileName):
        self._file_name = FileName

    def __repr__(self):
        txt = ""
        if self._file_name != "": 
            txt += "file name: '%s'\n" % self._file_name
        txt += "class:     '%s'\n" % self.class_name
        if self.open_for_derivation_f: 
            txt += "           (with virtual destructor)\n"
        txt += "namespace: '%s'\n" % repr(self.name_space)[1:-1]
        txt += "type(token_id)      = %s\n" % self.token_id_type.get_pure_code()
        txt += "type(column_number) = %s\n" % self.column_number_type.get_pure_code()
        txt += "type(line_number)   = %s\n" % self.line_number_type.get_pure_code()

        txt += "distinct members {\n"
        # '0' to make sure, that it works on an empty sequence too.
        L = self.distinct_members_type_name_length_max()
        for name, type_code in self.distinct_db.items():
            txt += "    %s%s %s\n" % (type_code.get_pure_code(), " " * (L - len(type_code.get_pure_code())), name)
        txt += "}\n"
        txt += "union members {\n"

        # '0' to make sure, that it works on an empty sequence too.
        L = self.union_members_type_name_length_max()
        for name, type_descr in self.union_db.items():
            if type(type_descr) == dict:
                txt += "    {\n"
                for sub_name, sub_type in type_descr.items():
                    txt += "        %s%s %s\n" % \
                           (sub_type.get_pure_code(), 
                            " " * (L - len(sub_type.get_pure_code())-4), 
                            sub_name)
                txt += "    }\n"
            else:
                txt += "    %s%s %s\n" % \
                       (type_descr.get_pure_code(), 
                        " " * (L - len(type_descr.get_pure_code())), 
                        name)
        txt += "}\n"

        # constructor / copy / destructor
        if self.constructor.get_pure_code() != "":
            txt += "constructor {\n"
            txt += self.constructor.get_code()
            txt += "}"
        
        if self.copy.get_pure_code() != "":
            txt += "copy {\n"
            txt += self.copy.get_code()
            txt += "}"

        if self.destructor.get_pure_code() != "":
            txt += "destructor {\n"
            txt += self.destructor.get_code()
            txt += "}"

        if self.body.get_pure_code() != "":
            txt += "body {\n"
            txt += self.body.get_code()
            txt += "}"

        return txt


class TokenTypeDescriptor(TokenTypeDescriptorCore):
    """The final product."""
    def __init__(self, Core):
        assert isinstance(Core, TokenTypeDescriptorCore)
        TokenTypeDescriptorCore.__init__(self, Core)

        # (*) Max length of variables etc. for pretty printing
        max_length = 0
        for type_descr in self.union_db.values():
            if type(type_descr) == dict:
                length = 4 + max([0] + map(lambda x: len(x.get_pure_code()), type_descr.values()))
            else:
                length = len(type_descr.get_pure_code())
            if length > max_length: max_length = length
        self.__union_members_type_name_length_max = max_length

        max_length = 0
        for name, type_descr in self.union_db.items():
            if type(type_descr) == dict:
                length = 4 + max([0] + map(lambda x: len(x), type_descr.keys()))
            else:
                length = len(name)
            if length > max_length: max_length = length
        self.__union_members_variable_name_length_max = max_length

        # 
        self.__distinct_members_type_name_length_max = \
               max([0] + map(lambda x: len(x.get_pure_code()), self.distinct_db.values()))
        self.__distinct_members_variable_name_length_max = \
               max([0] + map(lambda x: len(x), self.distinct_db.keys()))
        self.__type_name_length_max = \
               max(self.__distinct_members_type_name_length_max,
                   self.__union_members_type_name_length_max)
        self.__variable_name_length_max = \
               max(self.__distinct_members_variable_name_length_max,
                   self.__union_members_variable_name_length_max)

        # (*) Member DB: [member name] --> [type info, access info]
        db = {}
        for name, type_code in self.distinct_db.items():
            db[name] = [type_code, name]
        for name, type_descr in self.union_db.items():
            if type(type_descr) == dict:
                for sub_name, sub_type in type_descr.items():
                    db[sub_name] = [sub_type, "content." + name + "." + sub_name]
            else:
                db[name] = [type_descr, "content." + name]
        self.__member_db = db

    def get_file_name(self):
        return self._file_name

    def type_name_length_max(self):
        return self.__type_name_length_max

    def type_name_length_max(self):
        return self.__type_name_length_max

    def variable_name_length_max(self):
        return self.__variable_name_length_max

    def distinct_members_type_name_length_max(self):
        return self.__distinct_members_type_name_length_max

    def distinct_members_variable_name_length_max(self):
        return self.__distinct_members_variable_name_length_max

    def union_members_type_name_length_max(self):
        return self.__union_members_type_name_length_max

    def union_members_variable_name_length_max(self):
        return self.__union_members_variable_name_length_max

    def has_member(self, MemberName):
        return self.__member_db.has_key(MemberName)

    def get_member_db(self):
        return self.__member_db

    def get_member_access(self, MemberName):
        assert self.__member_db.has_key(MemberName), \
               "Member database does not provide member name '%s'.\n" % MemberName + \
               "Available: " + repr(self.__member_db.keys())
        return self.__member_db[MemberName][1]


TokenType_StandardMemberList = ["column_number", "line_number", "id"]

__data_name_index_counter = -1
def data_name_index_counter_get():
    global __data_name_index_counter
    __data_name_index_counter += 1
    return __data_name_index_counter

def parse(fh):
       
    descriptor = TokenTypeDescriptorCore()

    if not check(fh, "{"):
        error_msg("Missing opening '{' at begin of token_type definition", fh)

    already_defined_list = []
    position = fh.tell()
    result   = True
    while result == True:
        try: 
            x = fh.tell()
            fh.seek(x)
            result = parse_section(fh, descriptor, already_defined_list)
        except EndOfStreamException:
            fh.seek(position)
            error_msg("End of file reached while parsing token_type section.", fh)

        
    if not check(fh, "}"):
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type definition.", fh);

    result = TokenTypeDescriptor(descriptor)
    if result.get_member_db().keys() == []:
        error_msg("Section 'token_type' does not define any members.", fh)

    return result

def parse_section(fh, descriptor, already_defined_list):
    assert type(already_defined_list) == list

    SubsectionList = ["name", "file_name", 
                      "standard", "distinct", "union", 
                      "constructor", "destructor", "copy", "body",
                      "inheritable"]

    position = fh.tell()
    skip_whitespace(fh)
    word = read_identifier(fh)
    if word == "":
        fh.seek(position)
        if check(fh, "}"): 
            fh.seek(position) 
            return False
        error_msg("Missing token_type section ('standard', 'distinct', or 'union').", fh)

    verify_word_in_list(word, SubsectionList, 
                        "Subsection '%s' not allowed in token_type section." % word, fh)

    if word == "name":
        parse_token_type_name(fh, descriptor)

    elif word == "inheritable":
        descriptor.open_for_derivation_f = True
        verify_next_word(fh, ";")

    elif word == "file_name":
        verify_next_word(fh, "=")
        descriptor.set_file_name(read_until_letter(fh, ";"))
        verify_next_word(fh, ";")

    elif not check(fh, "{"):
        fh.seek(position)
        error_msg("Missing opening '{' at begin of token_type section '%s'." % word, fh);

    elif word in ["standard", "distinct", "union"]:
        if   word == "standard": parse_standard_members(fh, descriptor, already_defined_list)
        elif word == "distinct": parse_distinct_members(fh, descriptor, already_defined_list)
        elif word == "union":    parse_union_members(fh, descriptor, already_defined_list)

        if not check(fh, "}"):
            fh.seek(position)
            error_msg("Missing closing '}' at end of token_type section '%s'." % word, fh);

    else:
        # word in ["constructor", "destructor", "copy", "body"]
        try:
            code_fragment = parse_normal_code_fragment(fh, word)
        except:
            error_msg("End of file reached while parsing token_type section '%s'." % word, fh);

        if   word == "constructor": descriptor.constructor = code_fragment
        elif word == "destructor":  descriptor.destructor  = code_fragment
        elif word == "copy":        descriptor.copy        = code_fragment
        elif word == "body":        descriptor.body        = code_fragment
        else: 
            assert False, "This section should not be reachable"

    return True

def parse_token_type_name(fh, descriptor):
    # NOTE: Catching of EOF happens in caller: parse(...)
    if not check(fh, "="):
        error_msg("Missing '=' for token_type name specification.", fh)

    name_list = []
    while 1 + 1 == 2:
        skip_whitespace(fh)
        name = read_identifier(fh)

        if name == "": error_msg("Missing identifier in token type name.", fh)
        name_list.append(name)

        if   check(fh, "::"): continue
        elif check(fh, ";"):  break
        else:                 error_msg("Missing identifier in token type name.", fh)

    assert name_list != []
    descriptor.class_name = name_list[-1]
    descriptor.name_space = name_list[:-1]
            
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
        sub_db = parse_variable_definition_list(fh, "Concurrent union variables", already_defined_list)
        if not check(fh, "}"): 
            fh.seek(position)
            error_msg("Missing closing '}' after concurrent variable definition.", fh)
        return [ sub_db ]

    else:
        name_str = name_str.strip()
        if not check(fh, ":"): error_msg("Missing ':' after identifier '%s'." % name_str, fh)
        
        if fh.read(1).isspace() == False:
            error_msg("Missing whitespace after ':' after identifier '%s'.\n" % name_str \
                    + "The notation has to be: variable-name ':' type ';'.", fh)

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
        TypeStr = TypeCodeFragment.get_pure_code()
        if    TypeStr.find("string") != -1 \
           or TypeStr.find("vector") != -1 \
           or TypeStr.find("map")    != -1:
            error_msg("Numeric type required.\n" + \
                      "Example: <token_id: uint16_t>, Found: '%s'\n" % TypeStr, FileName, LineN)
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
        if not check(fh, ";"): 
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


