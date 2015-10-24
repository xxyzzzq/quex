#! /usr/bin/env python
import sys
import os
import subprocess
from StringIO import StringIO
from tempfile import mkstemp
sys.path.insert(0, os.environ["QUEX_PATH"])
#
from   quex.input.files.parser_data.counter        import CounterSetupLineColumn_Default
from   quex.input.files.mode                       import PatternActionInfo, IncidenceDB
from   quex.input.regular_expression.auxiliary     import PatternShorthand
import quex.input.regular_expression.engine        as     regex
from   quex.input.regular_expression.exception     import RegularExpressionException
from   quex.input.code.core                        import CodeTerminal
from   quex.engine.analyzer.door_id_address_label  import DoorID
from   quex.engine.analyzer.door_id_address_label  import dial_db
from   quex.engine.analyzer.terminal.core          import Terminal
from   quex.engine.analyzer.terminal.factory       import TerminalFactory
import quex.output.core.variable_db                as     variable_db
from   quex.output.core.variable_db                import VariableDB
from   quex.output.core.dictionary                 import db
import quex.output.core.state_router               as     state_router_generator
from   quex.engine.misc.string_handling            import blue_print
from   quex.engine.misc.tools                      import all_isinstance
import quex.output.cpp.core                        as     cpp_generator
#
import quex.blackboard as blackboard
from   quex.blackboard import E_Compression, \
                              setup as Setup, \
                              E_IncidenceIDs, \
                              signal_character_list, \
                              Lng

from   copy import deepcopy
# Switch: Removal of source and executable file
#         'False' --> No removal.
if False: REMOVE_FILES = True
else:     REMOVE_FILES = False

# Switch: Verbose debug output: 
#         'False' --> Verbose debug output
if True: # False: # True:
    SHOW_TRANSITIONS_STR  = ""
    SHOW_BUFFER_LOADS_STR = ""
else:
    SHOW_TRANSITIONS_STR  = "-DQUEX_OPTION_DEBUG_SHOW "  
    SHOW_BUFFER_LOADS_STR = "-DQUEX_OPTION_DEBUG_SHOW_LOADS -DQUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE"

# Switch: Turn off some warnings
#         'False' --> show (almost) all compiler warnings
if True:
    IGNORE_WARNING_F = True
else:
    IGNORE_WARNING_F = False

choices_list = ["ANSI-C-PlainMemory", "ANSI-C", "ANSI-C-CG", 
                "Cpp", "Cpp_StrangeStream", "Cpp-Template", "Cpp-Template-CG", 
                "Cpp-Path", "Cpp-PathUniform", "Cpp-Path-CG", 
                "Cpp-PathUniform-CG", "ANSI-C-PathTemplate"] 

def hwut_input(Title, Extra="", AddChoices=[], DeleteChoices=[]):
    global choices_list

    choices = choices_list + AddChoices
    for choice in DeleteChoices:
        if choice in choices: 
            del choices[choices.index(choice)]

    choices_str  = "CHOICES: " + repr(choices)[1:-1].replace("'", "") + ";"

    if "--hwut-info" in sys.argv:
        print Title + ";"
        print choices_str
        print "SAME;"
        sys.exit(0)

    if len(sys.argv) < 2:
        print "Choice argument requested. Run --hwut-info"
        sys.exit(0)

    if sys.argv[1] not in choices:
        print "Choice '%s' not acceptable." % sys.argv[1]
        sys.exit(0)

    return sys.argv[1]

def __Setup_init_language_database(Language):
    global Setup

    try:
        Setup.language = { 
            "ANSI-C-PlainMemory": "C",
            "ANSI-C-from-file":   "C",
            "ANSI-C":             "C",
            "ANSI-C-CG":          "C",
            "ANSI-C-PathTemplate": "C",
            "Cpp":                "C++", 
            "Cpp_StrangeStream":  "C++", 
            "Cpp-Template":       "C++", 
            "Cpp-Template-CG":    "C++", 
            "Cpp-Path":           "C++", 
            "Cpp-PathUniform":    "C++", 
            "Cpp-Path-CG":        "C++", 
            "Cpp-PathUniform-CG": "C++",
        }[Language]
    except:
        print "Error: missing language specifier: %s" % Language
        sys.exit()

    Setup.language_db = db[Setup.language]

def do(PatternActionPairList, TestStr, PatternDictionary={}, Language="ANSI-C-PlainMemory", 
       QuexBufferSize=15, # DO NOT CHANGE!
       SecondPatternActionPairList=[], QuexBufferFallbackN=-1, ShowBufferLoadsF=False,
       AssertsActionvation_str="-DQUEX_OPTION_ASSERTS"):

    BufferLimitCode = 0
    Setup.buffer_limit_code = BufferLimitCode
    Setup.buffer_element_specification_prepare()
    Setup.buffer_codec_prepare("unicode", None)

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
        Language = "ANSI-C"
        Setup.compression_type_list = [ E_Compression.PATH, E_Compression.TEMPLATE ]
        Setup.compression_template_min_gain = 0

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

    test_program = create_main_function(Language, TestStr, QuexBufferSize, 
                                        ComputedGotoF=computed_goto_f)

    state_machine_code = create_state_machine_function(PatternActionPairList, 
                                                       adapted_dict, 
                                                       BufferLimitCode)

    if len(SecondPatternActionPairList) != 0:
        dial_db.clear()
        CompileOptionStr += "-DQUEX_UNIT_TEST_SECOND_MODE"
        state_machine_code += create_state_machine_function(SecondPatternActionPairList, 
                                                            PatternDictionary, 
                                                            BufferLimitCode,
                                                            SecondModeF=True)

    if ShowBufferLoadsF:
        state_machine_code = "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS\n" + \
                             "#define __QUEX_OPTION_UNIT_TEST\n"                   + \
                             "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER\n"       + \
                             state_machine_code

    source_code =   create_common_declarations(Language, QuexBufferSize, TestStr, QuexBufferFallbackN, BufferLimitCode, ComputedGotoF=computed_goto_f) \
                  + state_machine_code \
                  + test_program

    # Verify, that Templates and Pathwalkers are really generated
    __verify_code_generation(FullLanguage, source_code)

    compile_and_run(Language, source_code, AssertsActionvation_str, CompileOptionStr)

def run_this(Str):
    try:
        fh_out = open("tmp.out", "w")
        fh_err = open("tmp.err", "w")
        call_list = Str.split()
        subprocess.call(call_list, stdout=fh_out, stderr=fh_err)
        fh_out.close()
        fh_err.close()
        fh_out = open("tmp.out", "r")
        fh_err = open("tmp.err", "r")
        txt = fh_err.read() + fh_out.read()
        # In the current version we forgive unused static functions
        postponed_list = []
        for line in txt.splitlines():
            if    line.find("DumpedTokenIdObject") != -1:
                postponed_list.append("## IGNORED: " + line.replace(os.environ["QUEX_PATH"] + "/quex/", ""))
                continue

            if    line.find("defined but not used") != -1 \
               or line.find("but never defined") != -1 \
               or line.find("unused variable") != -1 \
               or line.find("At top level") != -1 \
               or line.find("t global scope") != -1 \
               or (     (line.find("warning: unused variable") != -1 )                                           \
                   and ((line.find("path_") != -1 and not line.find("_end")) or line.find("pathwalker_") != -1)) \
               or (line.find("In function") != -1 and line.lower().find("error") == -1):
                    if IGNORE_WARNING_F: 
                        postponed_list.append("## IGNORED: " + line.replace(os.environ["QUEX_PATH"] + "/quex/", ""))
                        continue
            print line
        for line in postponed_list:
            print line
        os.remove("tmp.out")
        os.remove("tmp.err")
    except:
        print "<<execution failed>>"

def compile_and_run(Language, SourceCode, AssertsActionvation_str="", StrangeStream_str=""):
    executable_name, filename_tmp = compile(Language, SourceCode, AssertsActionvation_str, 
                                            StrangeStream_str)

    print "## (*) running the test"
    run_this("./%s" % executable_name)
    if REMOVE_FILES:
        try:    os.remove(filename_tmp)
        except: pass
        try:    os.remove(executable_name)
        except: pass

def compile(Language, SourceCode, AssertsActionvation_str="", StrangeStream_str=""):
    print "## (2) compiling generated engine code and test"    
    we_str = "-Wall -Werror -Wno-error=unused-function"
    if Language.find("ANSI-C") != -1:
        extension = ".c"
        # The '-Wvariadic-macros' shall remind us that we do not want use variadic macroes.
        # Because, some compilers do not swallow them!
        compiler  = "gcc -ansi -Wvariadic-macros %s" % we_str
    else:
        extension = ".cpp"
        compiler  = "g++ %s" % we_str

    fd, filename_tmp = mkstemp(extension, "tmp-", dir=os.getcwd())

    os.write(fd, SourceCode) 
    os.close(fd)    
    
    os.system("mv -f %s tmp%s" % (filename_tmp, extension)); 
    filename_tmp = "./tmp%s" % extension # DEBUG

    executable_name = "%s.exe" % filename_tmp
    # NOTE: QUEX_OPTION_ASSERTS is defined by AssertsActionvation_str (or not)
    try:    os.remove(executable_name)
    except: pass
    compile_str = compiler                + " " + \
                  StrangeStream_str       + " " + \
                  AssertsActionvation_str + " " + \
                  filename_tmp            + " " + \
                  "-I./. -I%s " % os.environ["QUEX_PATH"] + \
                  "-o %s "      % executable_name         + \
                  SHOW_TRANSITIONS_STR    + " " + \
                  SHOW_BUFFER_LOADS_STR


    # If computed gotos are involved, then make sure that the option is really active.
    # if compile_str.find("-DQUEX_OPTION_COMPUTED_GOTOS") != -1:
    #   run_this(compile_str + " -E") # -E --> expand macros
    #   content = open(filename_tmp, "rb").read()
    #   if content.find("QUEX_STATE_ROUTER"):
    #       print "##Error: computed gotos contain state router."
    #       sys.exit()

    print compile_str + "##" # DEBUG
    run_this(compile_str)
    sys.stdout.flush()

    return executable_name, filename_tmp

def create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF=False, ComputedGotoF=False):
    test_str = TestStr.replace("\"", "\\\"")
    test_str = test_str.replace("\n", "\\n\"\n\"")
    test_str = test_str.replace("\t", "\\t")

    txt = test_program_db[Language]
    txt = txt.replace("$$BUFFER_SIZE$$", repr(QuexBufferSize))
    txt = txt.replace("$$TEST_STRING$$", test_str)

    if CommentTestStrF: txt = txt.replace("$$COMMENT$$", "##")
    else:               txt = txt.replace("$$COMMENT$$", "")

    return txt

def create_common_declarations(Language, QuexBufferSize, TestStr, 
                               QuexBufferFallbackN=-1, BufferLimitCode=0, 
                               IndentationSupportF=False, TokenQueueF=False,
                               ComputedGotoF=False):
    # Determine the 'fallback' region size in the buffer
    if QuexBufferFallbackN == -1: 
        QuexBufferFallbackN = QuexBufferSize - 3
    if Language == "ANSI-C-PlainMemory": 
        QuexBufferFallbackN = max(0, len(TestStr) - 3) 

    # Parameterize the common declarations
    txt  = "#define   __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION\n"
    txt += "#define QUEX_TYPE_CHARACTER unsigned char\n" 
    txt += "#define __QUEX_OPTION_UNIT_TEST\n" 

    txt += test_program_common_declarations.replace("$$BUFFER_FALLBACK_N$$", 
                                                    repr(QuexBufferFallbackN))

    if ComputedGotoF:   
        txt = txt.replace("$$COMPUTED_GOTOS$$",    "/* Correct */")
        txt = txt.replace("$$NO_COMPUTED_GOTOS$$", "QUEX_ERROR_EXIT(\"QUEX_OPTION_COMPUTED_GOTOS not active!\\n\");")
    else:
        txt = txt.replace("$$COMPUTED_GOTOS$$",    "QUEX_ERROR_EXIT(\"QUEX_OPTION_COMPUTED_GOTOS active!\\n\");")
        txt = txt.replace("$$NO_COMPUTED_GOTOS$$", "/* Correct */")

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
    #                                     "*(me->buffer._read_p - 1)")
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

def nonsense_default_counter(FirstModeF):
    if FirstModeF:
        return   "static void\n" \
               + "__QUEX_COUNT_VOID(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd) {}\n" 
    else:
        return "" # Definition done before

test_program_common_declarations = """
$$__QUEX_OPTION_PLAIN_C$$
$$QUEX_OPTION_INDENTATION_TRIGGER$$
$$__QUEX_OPTION_TOKEN_QUEUE$$
#define QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN_DISABLED
#define QUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
#define QUEX_SETTING_BUFFER_MIN_FALLBACK_N     ((size_t)$$BUFFER_FALLBACK_N$$)
#define QUEX_SETTING_BUFFER_LIMIT_CODE         ((QUEX_TYPE_CHARACTER)$$BUFFER_LIMIT_CODE$$)
#define QUEX_OPTION_INCLUDE_STACK_DISABLED
#define QUEX_OPTION_STRING_ACCUMULATOR_DISABLED

#define QUEX_TKN_TERMINATION       0
#define QUEX_TKN_UNINITIALIZED     1
#define QUEX_TKN_INDENT            3
#define QUEX_TKN_DEDENT            4
#define QUEX_TKN_NODENT            5

#include <quex/code_base/test_environment/TestAnalyzer>
#include <quex/code_base/analyzer/asserts.i>
#include <quex/code_base/analyzer/struct/constructor.i>
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

#ifdef __QUEX_OPTION_PLAIN_C
quex_TestAnalyzer    lexer_state;
#else
TestAnalyzer         lexer_state;
#endif

static __QUEX_TYPE_ANALYZER_RETURN_VALUE  QUEX_NAME(Mr_analyzer_function)(QUEX_TYPE_ANALYZER*);
#ifdef QUEX_UNIT_TEST_SECOND_MODE
static __QUEX_TYPE_ANALYZER_RETURN_VALUE  QUEX_NAME(Mrs_analyzer_function)(QUEX_TYPE_ANALYZER*);
#endif

QUEX_NAMESPACE_MAIN_OPEN
QUEX_NAME(Mode) first_mode = {
      /* id                */ 0, 
      /* name              */ "Mode0", 
#     if      defined( QUEX_OPTION_INDENTATION_TRIGGER) \
         && ! defined(QUEX_OPTION_INDENTATION_DEFAULT_HANDLER)
      /* on_indentation    */ NULL,
#     endif
      /* on_entry          */ 0,
      /* on_exit           */ 0, 
#     ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
      /* has_base          */ NULL,
      /* has_entry_from)   */ NULL,
      /* has_exit_to       */ NULL,
#     endif
      /* analyzer_function */ QUEX_NAME(Mr_analyzer_function),
};

#ifdef QUEX_UNIT_TEST_SECOND_MODE
QUEX_NAME(Mode) second_mode = {
      /* id                */ 1, 
      /* name              */ "Mode1", 
#     if      defined( QUEX_OPTION_INDENTATION_TRIGGER) \
         && ! defined(QUEX_OPTION_INDENTATION_DEFAULT_HANDLER)
      /* on_indentation    */ NULL,
#     endif
      /* on_entry          */ 0,
      /* on_exit           */ 0, 
#     ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
      /* has_base          */ NULL,
      /* has_entry_from)   */ NULL,
      /* has_exit_to       */ NULL,
#     endif
      /* analyzer_function */ QUEX_NAME(Mrs_analyzer_function),
};
#endif

QUEX_NAME(Mode) *(QUEX_NAME(mode_db)[__QUEX_SETTING_MAX_MODE_CLASS_N]) = {
   &first_mode
#ifdef QUEX_UNIT_TEST_SECOND_MODE
   , &second_mode
#endif
};
QUEX_NAMESPACE_MAIN_CLOSE

#if defined(QUEX_OPTION_COMPUTED_GOTOS)
#   define DEAL_WITH_COMPUTED_GOTOS() \
           $$COMPUTED_GOTOS$$
#else
#   define DEAL_WITH_COMPUTED_GOTOS() \
           $$NO_COMPUTED_GOTOS$$
#endif

static int
run_test(const char* TestString, const char* Comment)
{
    (void)QUEX_NAME_TOKEN(DumpedTokenIdObject);
            
    printf("(*) test string: \\n'%s'%s\\n", TestString, Comment);
    printf("(*) result:\\n");

#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)

    while( lexer_state.current_analyzer_function(&lexer_state) == true );

#   else

    while( 1 + 1 == 2 ) {
        lexer_state.current_analyzer_function(&lexer_state);
        printf("---\\n");

        /* Print the token queue */
        while( QUEX_NAME(TokenQueue_is_empty)(&lexer_state._token_queue) == false ) {        
            switch( QUEX_NAME(TokenQueue_pop)(&lexer_state._token_queue)->_id ) {
            case QUEX_TKN_INDENT:      printf("INDENT\\n"); break;
            case QUEX_TKN_DEDENT:      printf("DEDENT\\n"); break;
            case QUEX_TKN_NODENT:      printf("NODENT\\n"); break;
            case QUEX_TKN_TERMINATION: return 0;
            default:                   printf("Unknown Token ID\\n"); break;
            }
        }
        QUEX_NAME(TokenQueue_reset)(&lexer_state._token_queue);
    }

#   endif

    printf("  ''\\n");
    return 0;
}
"""


test_program_db = { 
    "ANSI-C-PlainMemory": """
    #include <stdlib.h>

    int main(int argc, char** argv)
    {
        QUEX_TYPE_CHARACTER  TestString[] = "\\0$$TEST_STRING$$\\0";
        const size_t         MemorySize   = strlen((const char*)TestString+1) + 2;

        DEAL_WITH_COMPUTED_GOTOS();
        QUEX_NAME(from_memory)(&lexer_state, 
                               TestString, MemorySize, &TestString[MemorySize - 1]); 
        /**/
        return run_test((const char*)(TestString + 1), "$$COMMENT$$");
    }\n""",

    "ANSI-C": """
    #include <stdio.h>
    /* #include <quex/code_base/buffer/filler/BufferFiller_Plain> */

    int main(int argc, char** argv)
    {
        const char*       test_string = "$$TEST_STRING$$";
        FILE*             fh          = tmpfile();

        /* Write test string into temporary file */
        fwrite(test_string, strlen(test_string), 1, fh);
        fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

        DEAL_WITH_COMPUTED_GOTOS();
        QUEX_NAME(from_FILE)(&lexer_state, fh, 0x0);
        /**/
        (void)run_test(test_string, "$$COMMENT$$");

        fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
        return 0;
    }\n""",

    "Cpp": """
    #include <cstring>
    #include <sstream>
    #include <quex/code_base/buffer/filler/BufferFiller_Plain>

    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        istringstream* istr = new istringstream("$$TEST_STRING$$");

        DEAL_WITH_COMPUTED_GOTOS();
        lexer_state.from(istr, 0x0);

        return run_test("$$TEST_STRING$$", "$$COMMENT$$");
    }\n""",

    "Cpp_StrangeStream": """
    #include <cstring>
    #include <sstream>
    #include <quex/code_base/buffer/filler/BufferFiller_Plain>
    #include <quex/code_base/test_environment/StrangeStream>


    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        istringstream                  istr("$$TEST_STRING$$");
        StrangeStream<istringstream>*  strange_stream = new StrangeStream<istringstream>(&istr);

        DEAL_WITH_COMPUTED_GOTOS();
        lexer_state.from(strange_stream, 0x0);
        return run_test("$$TEST_STRING$$", "$$COMMENT$$");
    }\n""",

    "ANSI-C-from-file": """
    #include <stdio.h>
    #include <stdlib.h>

    int main(int argc, char** argv)
    {
        char        test_string[65536];
        FILE*       fh               = fopen(argv[1], "rb");
        size_t      buffer_size      = atoi(argv[2]);
        size_t      real_buffer_size = 0;

        (void)fread(test_string, 1, 65536, fh);
        fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

        DEAL_WITH_COMPUTED_GOTOS();
        QUEX_NAME(from_FILE)(&lexer_state, fh, 0x0);

        /* Double check, that buffer size has been set. */
        real_buffer_size = lexer_state.buffer._memory._back - lexer_state.buffer._memory._front + 1;
        printf("## buffer_size: { required: %i; real: %i; }\\n",
               (int)(buffer_size), (int)real_buffer_size);
        __quex_assert( real_buffer_size != buffer_size );

        (void)run_test(test_string, "$$COMMENT$$");

        fclose(fh); 
        return 0;
    }\n""",
}


def __verify_code_generation(FullLanguage, SourceCode):
    def check_occurence(String, Code):
        count_n = 0
        for line in Code.splitlines():
            if line.find(String) != -1:
               count_n += 1
               if count_n == 2: return True
        return False

    if FullLanguage.find("Path") != -1:
        # Check whether paths have been defined
        if check_occurence("path_base", SourceCode)  == False:
            print "ERROR: Option '%s' requires paths to be generated. None is." % FullLanguage
            sys.exit()
        else:
            print "##verified path:", FullLanguage

    elif FullLanguage.find("Template") != -1:
        # Check whether paths have been defined
        if check_occurence("template_", SourceCode) == False: 
            print "ERROR: Option '%s' requires templates to be generated. None is." % FullLanguage
            sys.exit()
        else:
            print "##verified template:", FullLanguage


