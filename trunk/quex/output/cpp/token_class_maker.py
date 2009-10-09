from   quex.frs_py.file_in                    import error_msg, \
                                                     write_safely_and_close, open_file_or_die, \
                                                     make_safe_identifier
from   quex.frs_py.string_handling            import blue_print
import quex.lexer_mode                        as lexer_mode
import quex.core_engine.generator.action_info as action_info
from   quex.input.setup                       import setup as Setup
from   quex.input.setup_parser                import __prepare_file_name

LanguageDB = Setup.language_db

def do():
    if lexer_mode.token_type_definition == None: return

    txt       = _do(lexer_mode.token_type_definition)

    file_name = lexer_mode.get_token_class_file_name(Setup)
    file_name = __prepare_file_name(file_name, FileStemIncludedF=True)
    write_safely_and_close(file_name, txt) 

def _do(Descr):
    # The following things must be ensured before the function is called
    assert Descr != None
    assert Descr.__class__.__name__ == "TokenTypeDescriptor"
    ## ALLOW: Descr.get_member_db().keys() == []

    TemplateFile = (Setup.QUEX_TEMPLATE_DB_DIR 
                    + "/token/CppTemplate.txt").replace("//","/")
    template_str = open_file_or_die(TemplateFile, Mode="rb").read()
    
    virtual_destructor_str = ""
    if Descr.open_for_derivation_f: virtual_destructor_str = "virtual "

    if Descr.copy.get_pure_code() == "":
        # Default copy operation: Plain Copy of token memory
        copy_str = "__QUEX_STD_memcpy((void*)this, (void*)&That, sizeof(QUEX_TYPE_TOKEN));\n"
    else:
        copy_str = Descr.copy.get_code()

    txt = blue_print(template_str,
                     [["$$DISTINCT_MEMBERS$$", get_distinct_members(Descr)],
                      ["$$UNION_MEMBERS$$",    get_union_members(Descr)],
                      ["$$SETTERS_GETTERS$$",  get_setter_getter(Descr)],
                      ["$$QUICK_SETTERS$$",    get_quick_setters(Descr)],
                      ["$$COPY$$",             copy_str],
                      ["$$CONSTRUCTOR$$",      Descr.constructor.get_code()],
                      ["$$DESTRUCTOR$$",       Descr.destructor.get_code()],
                      ["$$BODY$$",             Descr.body.get_code()],
                      ["$$NAMESPACE_OPEN$$",   LanguageDB["$namespace-open"](Descr.name_space)],
                      ["$$NAMESPACE_CLOSE$$",  LanguageDB["$namespace-close"](Descr.name_space)],
                      ["$$VIRTUAL_DESTRUCTOR$$", virtual_destructor_str],
                     ])
    return txt

def get_distinct_members(Descr):
    # '0' to make sure, that it works on an empty sequence too.
    TL = Descr.type_name_length_max()
    NL = Descr.variable_name_length_max()
    txt = ""
    for name, type_code in Descr.distinct_db.items():
        txt += __member(type_code, TL, name, NL)
    txt += action_info.get_return_to_source_reference()
    return txt

def get_union_members(Descr):
    # '0' to make sure, that it works on an empty sequence too.
    TL = Descr.type_name_length_max()
    NL = Descr.variable_name_length_max()
    if len(Descr.union_db) == 0: return ""
    
    txt = "    union {\n"
    for name, type_descr in Descr.union_db.items():
        if type(type_descr) == dict:
            txt += "        struct {\n"
            for sub_name, sub_type in type_descr.items():
                txt += __member(sub_type, TL, sub_name, NL, IndentationOffset=" " * 8)
            txt += "\n        } %s;\n" % name
        else:
            txt += __member(type_descr, TL, name, NL, IndentationOffset=" " * 4) + "\n"
    txt += "    } content;\n"
    txt += action_info.get_return_to_source_reference()
    return txt

def __member(TypeCode, MaxTypeNameL, VariableName, MaxVariableNameL, IndentationOffset=""):
    my_def  = IndentationOffset
    my_def += LanguageDB["$class-member-def"](TypeCode.get_pure_code(), MaxTypeNameL, 
                                              VariableName, MaxVariableNameL)
    return TypeCode.adorn_with_source_reference(my_def, ReturnToSourceF=False)

def get_setter_getter(Descr):
    """NOTE: All names are unique even in combined unions."""
    TL = Descr.type_name_length_max()
    NL = Descr.variable_name_length_max()
    variable_db = Descr.get_member_db()
    txt = ""
    for variable_name, info in variable_db.items():
        type_code = info[0]
        access    = info[1]
        type_str  = type_code.get_pure_code()
        my_def = "    %s%s get_%s() const %s{ return %s; }" \
               % (type_str,      " " * (TL - len(type_str)), 
                  variable_name, " " * ((NL + TL)- len(variable_name)), 
                  access)
        txt += type_code.adorn_with_source_reference(my_def, ReturnToSourceF=False)
        my_def = "    void%s set_%s(%s& Value) %s{ %s = Value; }" \
               % (" " * (TL - len("void")), 
                  variable_name, type_str, " " * (NL + TL - (len(type_str) + len(variable_name))), 
                  access)
        txt += type_code.adorn_with_source_reference(my_def, ReturnToSourceF=False)

    txt += action_info.get_return_to_source_reference()
    return txt

def get_quick_setters(Descr):
    """NOTE: All names are unique even in combined unions."""
    variable_db = Descr.get_member_db()
    used_signature_list = []

    def __quick_setter(ArgList):
        """ArgList = [ [Name, Type], [Name, Type], ...]
         
           NOTE: There cannot be two signatures of the same type specification.
                 This is so, since functions are overloaded, have the same name
                 and only identify with their types.
        """
        signature = map(lambda x: x[1].get_pure_code(), ArgList)
        if signature in used_signature_list:
            return ""
        txt = "    void set(const QUEX_TYPE_TOKEN_ID ID, "
        i = -1
        for name, type_info in ArgList:
            i += 1
            type_str = type_info.get_pure_code()
            if type_str.find("const") != -1: type_str = type_str[5:]
            txt += "const %s& Value%i, " % (type_str, i)
        txt = txt[:-2]
        txt += ")\n    { "
        txt += "_id = ID; "
        i = -1
        for name, type_info in ArgList:
            i += 1
            txt += "%s = Value%i; " % (variable_db[name][1], i)
        txt += "}\n"

        return txt

    def __combined_quick_setters(member_db, AllOnlyF=False):
        txt = ""
        member_list = member_db.items()
        if member_list == []: return ""

        # sort the members with respect to their occurence in the token_type section
        member_list.sort(lambda x, y: cmp(x[1].line_n, y[1].line_n))
        L = len(member_list)
        PresenceAll  = [ 1 ] * L
        if AllOnlyF: presence_map = PresenceAll
        else:        presence_map = [ 1 ] + [ 0 ] * (L - 1)  

        while 1 + 1 == 2:
            # build the argument list consisting of a permutation of distinct members
            arg_list = []
            for i in range(L):
                if presence_map[i]: arg_list.append(member_list[i])

            txt += __quick_setter(arg_list)

            # increment the presence map
            if presence_map == PresenceAll:
                break
            for i in range(L):
                if presence_map[i] == 1: presence_map[i] = 0
                else:                    presence_map[i] = 1; break

        return txt

    txt = ""

    # (*) Quick setters for distinct members
    txt += __combined_quick_setters(Descr.distinct_db)

    # (*) Quick setters for union members
    for name, type_info in Descr.union_db.items():
        if type(type_info) != dict: txt += __quick_setter([[name, type_info]])
        else:                       txt += __combined_quick_setters(type_info, AllOnlyF=True)


    return txt


