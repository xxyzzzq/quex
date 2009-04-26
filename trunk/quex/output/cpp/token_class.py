from quex.input.setup import setup as Setup
from quex.frs_py.file_in import error_msg
from quex.frs_py.string_handling import blue_print

LanguageDB = Setup.language_db

def do(Descr):
    Descr.__class__.__name__ == "TokenTypeDescription"

    txt = get_basic_template(Descr)
    txt = blue_print(txt,
                     [["$$DISTINCT_MEMBERS$$", get_distinct_members(Descr)],
                      ["$$UNION_MEMBERS$$",    get_union_members(Descr)],
                      ["$$SETTERS_GETTERS$$",  get_setter_getter(Descr)],
                      ["$$COPY$$",             Descr.copy.get_code()],
                      ["$$CONSTRUCTOR$$",      Descr.constructor.get_code()],
                      ["$$DESTRUCTOR$$",       Descr.destructor.get_code()],
                     ])
    return txt

def get_basic_template(Descr):
    TemplateFile = (Setup.QUEX_TEMPLATE_DB_DIR 
                    + "/template/TokenTemplate").replace("//","/")
    print "##", TemplateFile

    try:
        template_str = open(TemplateFile, "rb").read()
    except:
        error_msg("Error -- could not find token class template file.")
    
    namespace_str = LanguageDB["$namespace-ref"](Descr.name_space) 

    virtual_destructor_str = ""
    if Descr.open_for_derivation_f: virtual_destructor_str = "virtual "

    return blue_print(template_str, 
            [["$$TOKEN_CLASS$$",               Descr.class_name],
             ["$$TOKEN_ID_TYPE$$",             Descr.token_id_type.get_pure_code()],
             ["$$TOKEN_TYPE_WITH_NAMESPACE$$", namespace_str + Descr.class_name],
             ["$$TOKEN_TYPE$$",                Descr.class_name],
             ["$$VIRTUAL_DESTRUCTOR$$",        virtual_destructor_str],
             ["$$LINE_N_TYPE$$",               Descr.line_number_type.get_pure_code()],
             ["$$COLUMN_N_TYPE$$",             Descr.column_number_type.get_pure_code()]])

def get_distinct_members(Descr):
    # '0' to make sure, that it works on an empty sequence too.
    TL = Descr.type_name_length_max()
    NL = Descr.variable_name_length_max()
    txt = ""
    for name, type_code in Descr.distinct_db.items():
        txt += __member(type_code, TL, name, NL)
    return txt

def get_union_members(Descr):
    # '0' to make sure, that it works on an empty sequence too.
    TL = Descr.type_name_length_max()
    NL = Descr.variable_name_length_max()
    
    txt = "union {\n"
    for name, type_descr in Descr.union_db.items():
        if type(type_descr) == dict:
            txt += "    {\n"
            for sub_name, sub_type in type_descr.items():
                txt += __member(sub_type, TL, name, NL)
            txt += "    }\n"
        else:
            txt += __member(type_descr, TL, name, NL)
    txt += "}\n"
    return txt

def __member(TypeCode, MaxTypeNameL, VariableName, MaxVariableNameL):
    my_def = LanguageDB["$class-member-def"](TypeCode.get_pure_code(), MaxTypeNameL, 
                                             VariableName, MaxVariableNameL)
    return TypeCode.adorn_with_source_reference(my_def)

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
        my_def = "    %s%s %s() const     %s{ return %s; }" \
               % (type_str,      " " * (TL - len(type_str)), 
                  variable_name, " " * ((NL + TL)- len(variable_name)), 
                  access)
        txt += type_code.adorn_with_source_reference(my_def, ReturnToSourceF=False)
        my_def = "    void%s set_%s(%s Value) %s{ %s = Value; }" \
               % (" " * (TL - len("void")), 
                  variable_name, type_str, " " * (NL + TL - (len(type_str) + len(variable_name))), 
                  access)
        txt += type_code.adorn_with_source_reference(my_def, ReturnToSourceF=False)

    txt += type_code.get_return_to_source_reference()
    return txt


