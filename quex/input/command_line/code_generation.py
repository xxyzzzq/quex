def setup(command_line, argv):
    """RETURN:  True, if process needs to be started.
                False, if job is done.
    """
    global setup

    # (*) Classes and their namespace
    __setup_analyzer_class(setup)
    __setup_token_class(setup)
    __setup_token_id_prefix(setup)
    __setup_lexeme_null(setup)       # Requires 'token_class_name_space'

    # (*) Output programming language        
    setup.language = setup.language.upper()
    verify_word_in_list(setup.language, output_language_db.keys(),
                        "Programming language '%s' is not supported." % setup.language)
    setup.language_db  = output_language_db[setup.language]
    setup.extension_db = global_extension_db[setup.language]

    # Is the output file naming scheme provided by the extension database
    # (Validation must happen immediately)
    if setup.extension_db.has_key(setup.output_file_naming_scheme) == False:
        error_msg("File extension scheme '%s' is not provided for language '%s'.\n" \
                  % (setup.output_file_naming_scheme, setup.language) + \
                  "Available schemes are: %s." % repr(setup.extension_db.keys())[1:-1])

    # Before file names can be prepared, determine the output directory
    # If 'source packaging' is enabled and no output directory is specified
    # then take the directory of the source packaging.
    if setup.source_package_directory != "" and setup.output_directory == "":
        setup.output_directory = setup.source_package_directory

    if setup.buffer_codec in ["utf8", "utf16"]:
        setup.buffer_codec_transformation_info = setup.buffer_codec + "-state-split"

    elif len(setup.buffer_codec_file) != 0:
        try: 
            setup.buffer_codec = os.path.splitext(os.path.basename(setup.buffer_codec_file))[0]
        except:
            error_msg("cannot interpret string following '--codec-file'")

        setup.buffer_codec_transformation_info = codec_db.CodecTransformationInfo(FileName=setup.buffer_codec_file)

    elif setup.buffer_codec != "unicode":
        setup.buffer_codec_transformation_info = codec_db.CodecTransformationInfo(setup.buffer_codec)

    # (*) Output files
    if setup.language not in ["DOT"]:
        prepare_file_names(setup)

    if setup.buffer_byte_order == "<system>": 
        setup.buffer_byte_order = sys.byteorder 
        setup.byte_order_is_that_of_current_system_f = True
    else:
        setup.byte_order_is_that_of_current_system_f = False

    if setup.buffer_element_size == "wchar_t":
        error_msg("Since Quex version 0.53.5, 'wchar_t' can no longer be specified\n"
                  "with option '--buffer-element-size' or '-bes'. Please, specify\n"
                  "'--buffer-element-type wchar_t' or '--bet'.")

    if setup.buffer_element_type == "wchar_t":
        setup.converter_ucs_coding_name = "WCHAR_T"

    make_numbers(setup)

    # (*) Determine buffer element type and size (in bytes)
    if setup.buffer_element_size == -1:
        if global_character_type_db.has_key(setup.buffer_element_type):
            setup.buffer_element_size = global_character_type_db[setup.buffer_element_type][3]
        elif setup.buffer_element_type == "":
            setup.buffer_element_size = 1
        else:
            # If the buffer element type is defined, then here we know that it is 'unknown'
            # and Quex cannot know its size on its own.
            setup.buffer_element_size = -1

    if setup.buffer_element_type == "":
        if setup.buffer_element_size in [1, 2, 4]:
            setup.buffer_element_type = { 
                1: "uint8_t", 2: "uint16_t", 4: "uint32_t",
            }[setup.buffer_element_size]
        elif setup.buffer_element_size == -1:
            pass
        else:
            error_msg("Buffer element type cannot be determined for size '%i' which\n" \
                      % setup.buffer_element_size + 
                      "has been specified by '-b' or '--buffer-element-size'.")

    type_info = global_character_type_db.get(setup.buffer_element_type)
    if     type_info is not None and len(type_info) >= 4 \
       and type_info[3] != -1 and setup.buffer_element_size != -1 \
       and type_info[3] != setup.buffer_element_size:
        error_msg("\nBuffer element type ('--bet' or '--buffer-element-type') was set to '%s'.\n" \
                  % setup.buffer_element_type \
                  + "It is well known to be of size %s[byte]. However, the buffer element size\n" \
                  % type_info[3] \
                  + "('-b' or '--buffer-element-type') was specified as '%s'.\n\n" \
                  % setup.buffer_element_size \
                  + "Quex can continue, but the result is questionable.\n", \
                  DontExitF=True)

    setup.converter_f = False
    if setup.converter_iconv_f or setup.converter_icu_f or len(setup.converter_user_new_func) != 0:
        setup.converter_f = True

    # The only case where no converter helper is required is where ASCII 
    # (Unicode restricted to [0, FF] is used.
    setup.converter_helper_required_f = True
    if setup.converter_f == False and setup.buffer_element_size == 1 and setup.buffer_codec == "unicode":
        setup.converter_helper_required_f = False

    validation.do(setup, command_line, argv)

    if setup.converter_ucs_coding_name == "": 
        if global_character_type_db.has_key(setup.buffer_element_type):
            if setup.buffer_byte_order == "little": index = 1
            else:                                   index = 2
            setup.converter_ucs_coding_name = global_character_type_db[setup.buffer_element_type][index]

    if len(setup.token_id_foreign_definition_file) != 0: 
        if len(setup.token_id_foreign_definition_file) > 3: 
            error_msg("Option '--foreign-token-id-file' received > 3 followers.\n"
                      "Found: %s" % str(setup.token_id_foreign_definition_file)[1:-1])
        if len(setup.token_id_foreign_definition_file) > 1:
            setup.token_id_foreign_definition_file_region_begin_re = \
                    __compile_regular_expression(setup.token_id_foreign_definition_file[1], "token id region begin")
        if len(setup.token_id_foreign_definition_file) > 2:
            setup.token_id_foreign_definition_file_region_end_re = \
                    __compile_regular_expression(setup.token_id_foreign_definition_file[2], "token id region end")
        setup.token_id_foreign_definition_file = \
                setup.token_id_foreign_definition_file[0]

        CommentDelimiterList = [["//", "\n"], ["/*", "*/"]]
        parse_token_id_file(setup.token_id_foreign_definition_file, 
                            CommentDelimiterList)

    # (*) Compression Types
    compression_type_list = []
    for name, ctype in [("compression_template_f",         E_Compression.TEMPLATE),
                        ("compression_template_uniform_f", E_Compression.TEMPLATE_UNIFORM),
                        ("compression_path_f",             E_Compression.PATH),
                        ("compression_path_uniform_f",     E_Compression.PATH_UNIFORM)]:
        if command_line_args_defined(command_line, name):
            compression_type_list.append((command_line_arg_position(name), ctype))

    compression_type_list.sort(key=itemgetter(0))
    setup.compression_type_list = map(lambda x: x[1], compression_type_list)

    # (*) return setup ___________________________________________________________________
    return True

def __compile_regular_expression(Str, Name):
    tmp = Str.replace("*", "\\*")
    tmp = tmp.replace("?", "\\?")
    tmp = tmp.replace("{", "\\{")
    tmp = tmp.replace("}", "\\}")
    try:
        return re.compile(tmp)
    except:
        error_msg("Invalid %s: %s" % (Name, Str))

def __setup_analyzer_class(setup):
    """ X0::X1::X2::ClassName --> analyzer_class_name = ClassName
                                  analyzer_name_space = ["X0", "X1", "X2"]
        ::ClassName --> analyzer_class_name = ClassName
                        analyzer_name_space = []
        ClassName --> analyzer_class_name = ClassName
                      analyzer_name_space = ["quex"]
    """
    if setup.analyzer_class.find("::") == -1:
        setup.analyzer_class = "quex::%s" % setup.analyzer_class

    setup.analyzer_class_name, \
    setup.analyzer_name_space, \
    setup.analyzer_name_safe   = \
         read_namespaced_name(setup.analyzer_class, 
                              "analyzer class (options -o, --analyzer-class)")

    if setup.show_name_spaces_f:
        print "Analyzer: {"
        print "     class_name:  %s;" % setup.analyzer_class_name
        print "     name_space:  %s;" % repr(setup.analyzer_name_space)[1:-1]
        print "     name_prefix: %s;" % setup.analyzer_name_safe   
        print "}"

    setup.analyzer_derived_class_name,       \
    setup.analyzer_derived_class_name_space, \
    setup.analyzer_derived_class_name_safe = \
         read_namespaced_name(setup.analyzer_derived_class_name, 
                              "derived analyzer class (options --derived-class, --dc)",
                              AllowEmptyF=True)

def __setup_lexeme_null(setup):
    if len(setup.external_lexeme_null_object) != 0:
        lexeme_null_object = setup.external_lexeme_null_object
        default_name_space = setup.analyzer_name_space
    elif setup.token_class_only_f:
        lexeme_null_object = "LexemeNullObject"
        default_name_space = setup.token_class_name_space
    else:
        lexeme_null_object = "LexemeNullObject"
        default_name_space = setup.analyzer_name_space

    if lexeme_null_object.find("::") == -1:
        # By default, setup the token in the analyzer's namespace
        if len(setup.analyzer_name_space) != 0:
            name_space = reduce(lambda x, y: "%s::%s" % (x, y), default_name_space)
        else:
            name_space = ""
        lexeme_null_object = "%s::%s" % (name_space, lexeme_null_object)

    setup.lexeme_null_name,        \
    setup.lexeme_null_namespace,   \
    setup.lexeme_null_name_safe  = \
         read_namespaced_name(lexeme_null_object, 
                              "lexeme null object (options --lexeme-null-object, --lno)")
    setup.lexeme_null_full_name_cpp = "::" 
    for name in setup.lexeme_null_namespace:
        setup.lexeme_null_full_name_cpp += name + "::"
    setup.lexeme_null_full_name_cpp += setup.lexeme_null_name

def __setup_token_class(setup):
    """ X0::X1::X2::ClassName --> token_class_name = ClassName
                                  token_name_space = ["X0", "X1", "X2"]
        ::ClassName --> token_class_name = ClassName
                        token_name_space = []
        ClassName --> token_class_name = ClassName
                      token_name_space = analyzer_name_space
    """
    if setup.token_class.find("::") == -1:
        # By default, setup the token in the analyzer's namespace
        if len(setup.analyzer_name_space) != 0:
            analyzer_name_space = reduce(lambda x, y: "%s::%s" % (x, y), setup.analyzer_name_space)
        else:
            analyzer_name_space = ""
        setup.token_class = "%s::%s" % (analyzer_name_space, setup.token_class)

    # Token classes and derived classes have the freedom not to open a namespace,
    # thus no check 'if namespace == empty'.
    setup.token_class_name,       \
    setup.token_class_name_space, \
    setup.token_class_name_safe = \
         read_namespaced_name(setup.token_class, 
                              "token class (options --token-class, --tc)")

    if setup.show_name_spaces_f:
        print "Token: {"
        print "     class_name:  %s;" % setup.token_class_name
        print "     name_space:  %s;" % repr(setup.token_class_name_space)[1:-1]
        print "     name_prefix: %s;" % setup.token_class_name_safe   
        print "}"

    if setup.token_class_file != "":
        blackboard.token_type_definition = \
                TokenTypeDescriptorManual(setup.token_class_file,
                                          setup.token_class_name,
                                          setup.token_class_name_space,
                                          setup.token_class_name_safe,
                                          setup.token_id_type)

    #if len(setup.token_class_name_space) == 0:
    #    setup.token_class_name_space = deepcopy(setup.analyzer_name_space)

def __setup_token_id_prefix(setup):
    setup.token_id_prefix_plain,      \
    setup.token_id_prefix_name_space, \
    dummy                           = \
         read_namespaced_name(setup.token_id_prefix, 
                              "token prefix (options --token-id-prefix)", 
                              AllowEmptyF=True)

    if len(setup.token_id_prefix_name_space) != 0 and setup.language.upper() == "C":
         error_msg("Token id prefix cannot contain a namespaces if '--language' is set to 'C'.")

def prepare_file_names(setup):
    setup.output_file_stem = ""
    if setup.analyzer_name_space != ["quex"]:
        for name in setup.analyzer_name_space:
            setup.output_file_stem += name + "_"
    setup.output_file_stem += setup.analyzer_class_name

    setup.output_code_file          = __prepare_file_name("",               E_Files.SOURCE) 
    setup.output_header_file        = __prepare_file_name("",               E_Files.HEADER)
    setup.output_configuration_file = __prepare_file_name("-configuration", E_Files.HEADER)
    setup.output_token_id_file      = __prepare_file_name("-token_ids",     E_Files.HEADER)
    setup.output_token_class_file   = __prepare_file_name("-token",         E_Files.HEADER)
    if setup.token_class_only_f == False:
        setup.output_token_class_file_implementation = __prepare_file_name("-token",     E_Files.HEADER_IMPLEMTATION)
    else:
        setup.output_token_class_file_implementation = __prepare_file_name("-token",     E_Files.SOURCE)

    if   setup.buffer_codec == "utf8":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-utf8"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-utf8.i"

    elif setup.buffer_codec == "utf16":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-utf16"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-utf16.i"

    elif setup.buffer_codec == "utf32":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-utf32"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-utf32.i"

    elif setup.buffer_codec != "unicode":
        # Note, that the name may be set to 'None' if the conversion is utf8 or utf16
        # See Internal engine character encoding'
        setup.output_buffer_codec_header = \
            __prepare_file_name("-converter-%s" % setup.buffer_codec, E_Files.HEADER)
        setup.output_buffer_codec_header_i = \
            __prepare_file_name("-converter-%s" % setup.buffer_codec, E_Files.HEADER_IMPLEMTATION)
    else:
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-unicode-buffer"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-unicode-buffer.i"

def make_numbers(setup):
    setup.compression_template_min_gain = __get_integer("compression_template_min_gain")
    setup.buffer_limit_code             = __get_integer("buffer_limit_code")
    setup.path_limit_code               = __get_integer("path_limit_code")

    setup.token_id_counter_offset       = __get_integer("token_id_counter_offset")
    setup.token_queue_size              = __get_integer("token_queue_size")
    setup.token_queue_safety_border     = __get_integer("token_queue_safety_border")
    setup.buffer_element_size           = __get_integer("buffer_element_size")

def __get_integer(MemberName):
    return __get_integer_core(MemberName, setup.__dict__[MemberName])

def __get_integer_core(MemberName, ValueStr):
    if type(ValueStr) == int: 
        return ValueStr
    result = read_integer(StringIO(ValueStr))
    if result is None:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an integer for '%s'.\n" % (ValueStr, option_name) + \
                  "Use prefix '0x' for hexadecimal numbers.\n" + \
                  "           '0o' for octal numbers.\n"       + \
                  "           '0b' for binary numbers.\n"      + \
                  "           '0r' for roman numbers.\n"      + \
                  "           and no prefix for decimal numbers.")
    return result

def __prepare_file_name(Suffix, ContentType):
    global setup
    assert ContentType in E_Files

    # Language + Extenstion Scheme + ContentType --> name of extension
    ext = setup.extension_db[setup.output_file_naming_scheme][ContentType]

    file_name = setup.output_file_stem + Suffix + ext

    if setup.output_directory == "": return file_name
    else:                            return os.path.normpath(setup.output_directory + "/" + file_name)

