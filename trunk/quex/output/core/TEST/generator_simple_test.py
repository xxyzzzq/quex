# This file is an attempt to simplify the generation of tests. 
# The currently used generator_test is flooded with work-arounds
# and adaptions that make the process intransparent.

def do(PatternActionPairList, TestStr, PatternDictionary={}, 
       Language="ANSI-C-PlainMemory", 
       QuexBufferSize=15, # DO NOT CHANGE!
       QuexBufferFallbackN=-1, ShowBufferLoadsF=False,
       AssertsActionvation_str="-DQUEX_OPTION_ASSERTS"):

    setup_buffer(BufferLimitCode)

    setup_language(Language)

    pattern_db         = setup_pattern_db(PatternDictionary) 
                       
    test_program       = create_main_function(Language, TestStr, QuexBufferSize, 
                                              ComputedGotoF=computed_goto_f)

    state_machine_code = create_state_machine_function(PatternActionPairList, 
                                                       pattern_db, 
                                                       BufferLimitCode)

    source_code =   create_common_declarations(Language, QuexBufferSize, TestStr, QuexBufferFallbackN, BufferLimitCode) \
                  + state_machine_code \
                  + test_program

    # Verify, that Templates and Pathwalkers are really generated
    __verify_code_generation(FullLanguage, source_code)

    compile_and_run(Language, source_code, AssertsActionvation_str, CompileOptionStr)

def setup_buffer(BufferLimitCode):
    BufferLimitCode = 0
    Setup.buffer_limit_code = BufferLimitCode
    Setup.buffer_element_specification_prepare()
    Setup.buffer_codec_prepare("unicode", None)

def setup_language(Language):
    __Setup_init_language_database(Language)

    CompileOptionStr = ""
    computed_goto_f  = False
    FullLanguage     = Language
    if Language.find("StrangeStream") != -1:
        CompileOptionStr += " -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION "

    if Language.find("-CG") != -1:
        Language = Language.replace("-CG", "")
        CompileOptionStr += " -DQUEX_OPTION_COMPUTED_GOTOS "
        computed_goto_f   = True

    if Language == "Cpp-Template":
        Language = "Cpp"
        # Shall template compression be used?
        Setup.compression_type_list = [ E_Compression.TEMPLATE ]
        Setup.compression_template_min_gain = 0

    elif Language == "Cpp-Path":
        Language = "Cpp"
        Setup.compression_type_list = [ E_Compression.PATH ]

    elif Language == "Cpp-PathUniform":
        Language = "Cpp"
        Setup.compression_type_list = [ E_Compression.PATH_UNIFORM ]

    elif Language == "ANSI-C-PathTemplate":
        Language = "Cpp"
        Setup.compression_type_list = [ E_Compression.PATH, E_Compression.TEMPLATE ]
        Setup.compression_template_min_gain = 0

def setup_pattern_db(PatternDictionary):
    try:
        adapted_dict = {}
        for key, regular_expression in PatternDictionary.items():
            string_stream = StringIO(regular_expression)
            pattern       = regex.do(string_stream, adapted_dict)
            # It is ESSENTIAL that the state machines of defined patterns do not 
            # have origins! Actually, there are not more than patterns waiting
            # to be applied in regular expressions. The regular expressions 
            # can later be origins.
            assert pattern.sm.has_origins() == False

            adapted_dict[key] = PatternShorthand(key, pattern.sm)

    except RegularExpressionException, x:
        print "Dictionary Creation:\n" + repr(x)

    return adapted_dict

def create_common_declarations(Language, QuexBufferSize, TestStr, 
                               QuexBufferFallbackN=-1, BufferLimitCode=0, 
                               IndentationSupportF=False, TokenQueueF=False):
    # Determine the 'fallback' region size in the buffer
    if QuexBufferFallbackN == -1: 
        QuexBufferFallbackN = QuexBufferSize - 3
    if Language == "ANSI-C-PlainMemory": 
        QuexBufferFallbackN = max(0, len(TestStr) - 3) 


    def activate(txt, Option, Value):
        return txt.replace("$$#define %s$$" % Option, Option)

    txt = ""
    if ShowBufferLoadsF:
        txt += "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS\n" \
               "#define __QUEX_OPTION_UNIT_TEST\n"                   \
               "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER\n"       

    # Parameterize the common declarations
    txt += test_program_common_declarations.replace("$$BUFFER_FALLBACK_N$$", 
                                                    repr(QuexBufferFallbackN))

    txt = txt.replace("$$BUFFER_LIMIT_CODE$$", repr(BufferLimitCode))

    replace_str = "#define QUEX_OPTION_INDENTATION_TRIGGER"
    if not IndentationSupportF: replace_str = "/* %s */" % replace_str
    txt = txt.replace("$$QUEX_OPTION_INDENTATION_TRIGGER$$", replace_str)
       
    replace_str = "#define QUEX_OPTION_TOKEN_POLICY_SINGLE_DISABLED\n" + \
                  "#define QUEX_OPTION_TOKEN_POLICY_QUEUE"
    if not TokenQueueF: replace_str = "/* %s */" % replace_str.replace("\n", "\n * ")
    txt = txt.replace("$$__QUEX_OPTION_TOKEN_QUEUE$$", replace_str)


    replace_str = "#define __QUEX_OPTION_PLAIN_C"
    if Language not in ["ANSI-C", "ANSI-C-PlainMemory", "ANSI-C-from-file"]: replace_str = "/* %s */" % replace_str
    txt = txt.replace("$$__QUEX_OPTION_PLAIN_C$$", replace_str)

    return txt

def create_state_machine_function(PatternActionPairList, PatternDictionary, 
                                  BufferLimitCode, SecondModeF=False):

    # (*) Initialize address handling
    dial_db.clear()     # BEFORE constructor of generator; 
    variable_db.variable_db.init()  # because constructor creates some addresses.
    blackboard.required_support_begin_of_line_set()

    def action(ThePattern, PatternName): 
        txt = []
        if ThePattern.bipd_sm is not None:
            TerminalFactory.do_bipd_entry_and_return(txt, pattern)

        txt.append("%s\n" % Lng.STORE_LAST_CHARACTER(blackboard.required_support_begin_of_line()))
        txt.append("%s\n" % Lng.LEXEME_TERMINATING_ZERO_SET(True))
        txt.append('printf("%19s  \'%%s\'\\n", Lexeme); fflush(stdout);\n' % PatternName)

        if   "->1" in PatternName: txt.append("me->current_analyzer_function = QUEX_NAME(Mr_analyzer_function);\n")
        elif "->2" in PatternName: txt.append("me->current_analyzer_function = QUEX_NAME(Mrs_analyzer_function);\n")

        if "CONTINUE" in PatternName: txt.append("")
        elif "STOP" in PatternName:   txt.append("return false;\n")
        else:                         txt.append("return true;\n")


        txt.append("%s\n" % Lng.GOTO(DoorID.continue_with_on_after_match()))
        ## print "#", txt
        return CodeTerminal(txt)
    
    # -- Display Setup: Patterns and the related Actions
    print "(*) Lexical Analyser Patterns:"
    for pair in PatternActionPairList:
        print "%20s --> %s" % (pair[0], pair[1])

    if not SecondModeF:  sm_name = "Mr"
    else:                sm_name = "Mrs"

    Setup.analyzer_class_name = sm_name
    
    pattern_action_list = [
        (regex.do(pattern_str, PatternDictionary), action_str)
        for pattern_str, action_str in PatternActionPairList
    ]
    
    support_begin_of_line_f = False
    for pattern, action_str in pattern_action_list:
        support_begin_of_line_f |= pattern.pre_context_trivial_begin_of_line_f

    for pattern, action_str in pattern_action_list:
        pattern.prepare_count_info(CounterSetupLineColumn_Default(), CodecTrafoInfo=None)
        pattern.mount_post_context_sm()
        pattern.mount_pre_context_sm()
        pattern.cut_character_list(signal_character_list(Setup))

    # -- PatternList/TerminalDb
    #    (Terminals can only be generated after the 'mount procedure', because, 
    #     the bipd_sm is generated through mounting.)
    on_failure              = CodeTerminal(["return false;\n"])
    support_begin_of_line_f = False
    terminal_db             = {
        E_IncidenceIDs.MATCH_FAILURE: Terminal(on_failure, "FAILURE"),
        E_IncidenceIDs.END_OF_STREAM: Terminal(on_failure, "END_OF_STREAM"),
    }
    terminal_db[E_IncidenceIDs.MATCH_FAILURE].set_incidence_id(E_IncidenceIDs.MATCH_FAILURE)
    terminal_db[E_IncidenceIDs.END_OF_STREAM].set_incidence_id(E_IncidenceIDs.END_OF_STREAM)
    for pattern, action_str in pattern_action_list:
        name     = TerminalFactory.name_pattern_match_terminal(pattern.pattern_string())
        terminal = Terminal(action(pattern, action_str), name)
        terminal.set_incidence_id(pattern.incidence_id())
        terminal_db[pattern.incidence_id()] = terminal

    # -- create default action that prints the name and the content of the token
    #    store_last_character_str = ""
    #    if support_begin_of_line_f:
    #        store_last_character_str  = "    %s = %s;\n" % \
    #                                    ("me->buffer._character_before_lexeme_start", 
    #                                     "*(me->buffer._input_p - 1)")
    #    set_terminating_zero_str  = "    QUEX_LEXEME_TERMINATING_ZERO_SET(&me->buffer);\n"
    #    prefix = store_last_character_str + set_terminating_zero_str

    print "## (1) code generation"    

    pattern_list = [ pattern for pattern, action_str in pattern_action_list ]
    function_body, variable_definitions = cpp_generator.do_core(pattern_list, terminal_db)
    function_body += "if(0) { __QUEX_COUNT_VOID((QUEX_TYPE_ANALYZER*)0, (QUEX_TYPE_CHARACTER*)0, (QUEX_TYPE_CHARACTER*)0); }\n"
    function_txt                        = cpp_generator.wrap_up(sm_name, function_body, 
                                                                variable_definitions, 
                                                                ModeNameList=[])

    assert all_isinstance(function_txt, str)

    return   "#define  __QUEX_OPTION_UNIT_TEST\n" \
           + nonsense_default_counter(not SecondModeF) \
           + "".join(function_txt)

test_program_common_declarations = """
#define __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
#define QUEX_TYPE_CHARACTER unsigned char

$$__QUEX_OPTION_PLAIN_C$$
$$QUEX_OPTION_INDENTATION_TRIGGER$$
$$__QUEX_OPTION_TOKEN_QUEUE$$
#define QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN_DISABLED
#define QUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
#define QUEX_OPTION_INCLUDE_STACK_DISABLED
#define QUEX_OPTION_STRING_ACCUMULATOR_DISABLED
#define QUEX_SETTING_BUFFER_MIN_FALLBACK_N     ((size_t)$$BUFFER_FALLBACK_N$$)
#define QUEX_SETTING_BUFFER_LIMIT_CODE         ((QUEX_TYPE_CHARACTER)$$BUFFER_LIMIT_CODE$$)

#define QUEX_TKN_TERMINATION       0
#define QUEX_TKN_UNINITIALIZED     1
#define QUEX_TKN_INDENT            3
#define QUEX_TKN_DEDENT            4
#define QUEX_TKN_NODENT            5

#include <quex/code_base/test_environment/TestAnalyzer>
#include <quex/code_base/analyzer/asserts.i>
#include <quex/code_base/analyzer/member/mode-handling.i>
#ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue.i>
#endif

#include <quex/code_base/single.i>

#if ! defined (__QUEX_OPTION_PLAIN_C)
    using namespace quex;
#endif

QUEX_NAMESPACE_LEXEME_NULL_OPEN     
QUEX_TYPE_CHARACTER   QUEX_LEXEME_NULL_IN_ITS_NAMESPACE;
QUEX_NAMESPACE_LEXEME_NULL_CLOSE     

QUEX_NAMESPACE_MAIN_OPEN
static QUEX_TYPE_TOKEN_ID  QUEX_NAME_TOKEN(DumpedTokenIdObject) = (QUEX_TYPE_TOKEN_ID)0;
QUEX_NAMESPACE_MAIN_CLOSE

#ifndef RETURN
#   if ! defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
       QUEX_TYPE_TOKEN_ID    __self_result_token_id;
#      define RETURN    do { return __self_result_token_id; } while(0)
#   else                
#      define RETURN    return
#   endif
#endif

static __QUEX_TYPE_ANALYZER_RETURN_VALUE QUEX_NAME(Mr_analyzer_function)(QUEX_TYPE_ANALYZER*);

static int
run_test(const char* TestString, const char* Comment, QUEX_TYPE_ANALYZER* lexer)
{
    lexer->current_analyzer_function = QUEX_NAME(Mr_analyzer_function);

    printf("(*) test string: \\n'%s'%s\\n", TestString, Comment);
    printf("(*) result:\\n");

#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)

    while( lexer->current_analyzer_function(lexer) == true );

#   else

    while( 1 + 1 == 2 ) {
        lexer->current_analyzer_function(lexer);
        printf("---\\n");

        /* Print the token queue */
        while( QUEX_NAME(TokenQueue_is_empty)(&lexer->_token_queue) == false ) {        
            switch( QUEX_NAME(TokenQueue_pop)(&lexer->_token_queue)->_id ) {
            case QUEX_TKN_INDENT:      printf("INDENT\\n"); break;
            case QUEX_TKN_DEDENT:      printf("DEDENT\\n"); break;
            case QUEX_TKN_NODENT:      printf("NODENT\\n"); break;
            case QUEX_TKN_TERMINATION: return 0;
            default:                   printf("Unknown Token ID\\n"); break;
            }
        }
        QUEX_NAME(TokenQueue_reset)(&lexer->_token_queue);
    }

#   endif

    printf("  ''\\n");
    return 0;
}
"""
