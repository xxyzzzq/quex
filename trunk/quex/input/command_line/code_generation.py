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


