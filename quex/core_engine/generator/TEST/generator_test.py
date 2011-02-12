#! /usr/bin/env python
import sys
import os
import subprocess
from StringIO import StringIO
from tempfile import mkstemp
sys.path.insert(0, os.environ["QUEX_PATH"])
#
from quex.frs_py.string_handling import blue_print
from quex.exception              import RegularExpressionException
from quex.lexer_mode             import PatternShorthand
#
from   quex.core_engine.generator.languages.core import db
from   quex.core_engine.generator.languages.cpp  import  __local_variable_definitions
from   quex.core_engine.generator.action_info    import PatternActionInfo, CodeFragment
import quex.core_engine.generator.core                  as generator
# import quex.core_engine.generator.skipper.core          as skipper
import quex.core_engine.generator.skipper.character_set as character_set_skipper
import quex.core_engine.generator.skipper.range         as range_skipper
import quex.core_engine.generator.skipper.nested_range  as nested_range_skipper
import quex.core_engine.regular_expression.core         as regex
#
from   quex.input.setup import setup as Setup

# Switch: Removal of source and executable file
#         'False' --> No removal.
if False: REMOVE_FILES = True
else:    REMOVE_FILES = False

# Switch: Verbose debug output: 
#         'False' --> Verbose debug output
if True:
    SHOW_TRANSITIONS_STR  = ""
    SHOW_BUFFER_LOADS_STR = ""
else:
    SHOW_TRANSITIONS_STR  = "-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS "  
    SHOW_BUFFER_LOADS_STR = "-D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS " 


choices_list = ["ANSI-C-PlainMemory", "ANSI-C", "ANSI-C-CG", 
                "Cpp", "Cpp_StrangeStream", "Cpp-Template", "Cpp-Template-CG", 
                "Cpp-Path", "Cpp-PathUniform", "Cpp-Path-CG", 
                "Cpp-PathUniform-CG"] 

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
            "ANSI-C":             "C",
            "ANSI-C-CG":          "C",
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

    __Setup_init_language_database(Language)

    CompileOptionStr = ""
    if Language.find("StrangeStream") != -1:
        CompileOptionStr += " -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION "

    if Language.find("-CG") != -1:
        Language = Language.replace("-CG", "")
        CompileOptionStr += " -DQUEX_OPTION_COMPUTED_GOTOS "

    if Language == "Cpp-Template":
        Language = "Cpp"
        # Shall template compression be used?
        Setup.compression_template_f    = True
        Setup.compression_template_coef = 0.1

    elif Language == "Cpp-Path":
        Language = "Cpp"
        Setup.compression_path_f = True

    elif Language == "Cpp-PathUniform":
        Language = "Cpp"
        Setup.compression_path_uniform_f = True

    try:
        adapted_dict = {}
        for key, regular_expression in PatternDictionary.items():
            string_stream = StringIO(regular_expression)
            state_machine = regex.do(string_stream, adapted_dict)
            # It is ESSENTIAL that the state machines of defined patterns do not 
            # have origins! Actually, there are not more than patterns waiting
            # to be applied in regular expressions. The regular expressions 
            # can later be origins.
            assert state_machine.has_origins() == False

            adapted_dict[key] = PatternShorthand(key, state_machine)

    except RegularExpressionException, x:
        print "Dictionary Creation:\n" + repr(x)

    test_program = create_main_function(Language, TestStr, QuexBufferSize)

    state_machine_code = create_state_machine_function(PatternActionPairList, 
                                                       adapted_dict, 
                                                       BufferLimitCode)

    if SecondPatternActionPairList != []:
        state_machine_code += create_state_machine_function(SecondPatternActionPairList, 
                                                            PatternDictionary, 
                                                            BufferLimitCode,
                                                            SecondModeF=True)


    if ShowBufferLoadsF:
        state_machine_code = "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS\n" + \
                             "#define __QUEX_OPTION_UNIT_TEST\n"                   + \
                             "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER\n"       + \
                             state_machine_code

    source_code =   create_common_declarations(Language, QuexBufferSize, TestStr, QuexBufferFallbackN, BufferLimitCode) \
                  + state_machine_code \
                  + test_program

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
        for line in txt.split("\n"):
            if    line.find("defined but not used") != -1 \
               or line.find("but never defined") != -1 \
               or line.find("t global scope") != -1 \
               or     (line.find("warning: unused variable") != -1 )          \
                  and ((line.find("path_") != -1 and not line.find("_end")) or line.find("pathwalker_") != -1) \
               or (line.find("In function") != -1 and line.lower().find("error") == -1):
                postponed_list.append("## IGNORED: " + line.replace(os.environ["QUEX_PATH"] + "/quex/", ""))
            else:
                print line
        for line in postponed_list:
            print line
        os.remove("tmp.out")
        os.remove("tmp.err")
    except:
        print "<<execution failed>>"

def compile_and_run(Language, SourceCode, AssertsActionvation_str="", StrangeStream_str=""):
    print "## (*) compiling generated engine code and test"    
    if Language in ["ANSI-C", "ANSI-C-PlainMemory"]:
        extension = ".c"
        # The '-Wvariadic-macros' shall remind us that we do not want use variadic macroes.
        # Because, some compilers do not swallow them!
        compiler  = "gcc -ansi -Wvariadic-macros -Wall"
    else:
        extension = ".cpp"
        compiler  = "g++ -Wall"

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
                  # "-ggdb"                 + " " + \

    print compile_str + "##" # DEBUG
    run_this(compile_str)
    sys.stdout.flush()

    print "## (*) running the test"
    run_this("./%s" % executable_name)
    if REMOVE_FILES:
        try:    os.remove(filename_tmp)
        except: pass
        try:    os.remove(executable_name)
        except: pass

def create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF=False):
    test_str = TestStr.replace("\"", "\\\"")
    test_str = test_str.replace("\n", "\\n\"\n\"")

    txt = test_program_db[Language]
    txt = txt.replace("$$BUFFER_SIZE$$", repr(QuexBufferSize))
    txt = txt.replace("$$TEST_STRING$$", test_str)
    if CommentTestStrF: txt = txt.replace("$$COMMENT$$", "##")
    else:               txt = txt.replace("$$COMMENT$$", "")

    return txt

def create_common_declarations(Language, QuexBufferSize, TestStr, QuexBufferFallbackN=-1, BufferLimitCode=0, IndentationSupportF=False, TokenQueueF=False):
    # Determine the 'fallback' region size in the buffer
    if QuexBufferFallbackN == -1: 
        QuexBufferFallbackN = QuexBufferSize - 3
    if Language == "ANSI-C-PlainMemory": 
        QuexBufferFallbackN = max(0, len(TestStr) - 3) 

    # Parameterize the common declarations
    txt = test_program_common_declarations.replace("$$BUFFER_FALLBACK_N$$", repr(QuexBufferFallbackN))
    txt = "#define QUEX_TYPE_CHARACTER unsigned char\n" + txt
    txt = txt.replace("$$BUFFER_LIMIT_CODE$$", repr(BufferLimitCode))

    replace_str = "#define QUEX_OPTION_INDENTATION_TRIGGER"
    if not IndentationSupportF: replace_str = "/* %s */" % replace_str
    txt = txt.replace("$$QUEX_OPTION_INDENTATION_TRIGGER$$", replace_str)
       
    replace_str = "#define QUEX_OPTION_TOKEN_POLICY_SINGLE_DISABLED\n" + \
                  "#define QUEX_OPTION_TOKEN_POLICY_QUEUE"
    if not TokenQueueF: replace_str = "/* %s */" % replace_str.replace("\n", "\n * ")
    txt = txt.replace("$$__QUEX_OPTION_TOKEN_QUEUE$$", replace_str)


    replace_str = "#define __QUEX_OPTION_PLAIN_C"
    if Language not in ["ANSI-C", "ANSI-C-PlainMemory"]: replace_str = "/* %s */" % replace_str
    txt = txt.replace("$$__QUEX_OPTION_PLAIN_C$$", replace_str)

    return txt

def create_state_machine_function(PatternActionPairList, PatternDictionary, 
                                  BufferLimitCode, SecondModeF=False):
    on_failure_action = "return false;"

    # -- produce some visible output about the setup
    print "(*) Lexical Analyser Patterns:"
    for pair in PatternActionPairList:
        print "%20s --> %s" % (pair[0], pair[1])
    # -- create default action that prints the name and the content of the token
    try:
        PatternActionPairList = map(lambda x: 
                                    PatternActionInfo(regex.do(x[0], PatternDictionary), 
                                                      CodeFragment(action(x[1]), RequireTerminatingZeroF=True)),
                                    PatternActionPairList)
    except RegularExpressionException, x:
        print "Regular expression parsing:\n" + x.message
        sys.exit(0)

    support_begin_of_line_f = False
    for entry in PatternActionPairList:
        if entry.pattern_state_machine().core().pre_context_begin_of_line_f():
            support_begin_of_line_f = True
            break

    print "## (1) code generation"    
    txt = "#define  __QUEX_OPTION_UNIT_TEST\n"

    if not SecondModeF:  sm_name = "Mr"
    else:                sm_name = "Mrs"

    txt += generator.do(PatternActionPairList, 
                        StateMachineName       = sm_name + "_UnitTest",
                        OnFailureAction        = PatternActionInfo(None, on_failure_action), 
                        EndOfStreamAction      = PatternActionInfo(None, on_failure_action), 
                        PrintStateMachineF     = True,
                        AnalyserStateClassName = sm_name,
                        StandAloneAnalyserF    = True, 
                        SupportBeginOfLineF    = support_begin_of_line_f)

    return generator.delete_unused_labels(txt)

def create_customized_analyzer_function(Language, TestStr, EngineSourceCode, 
                                        QuexBufferSize, CommentTestStrF, ShowPositionF, EndStr, MarkerCharList,
                                        LocalVariableDB, IndentationSupportF=False, TokenQueueF=False):

    txt  = create_common_declarations(Language, QuexBufferSize, TestStr, 
                                      IndentationSupportF=IndentationSupportF, 
                                      TokenQueueF=TokenQueueF)
    txt += my_own_mr_unit_test_function(ShowPositionF, MarkerCharList, EngineSourceCode, EndStr, LocalVariableDB)
    txt += create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF)

    return txt

def create_character_set_skipper_code(Language, TestStr, TriggerSet, QuexBufferSize=1024):

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    skipper_code, local_variable_db = character_set_skipper.get_skipper(TriggerSet)

    marker_char_list = []
    for interval in TriggerSet.get_intervals():
        for char_code in range(interval.begin, interval.end):
            marker_char_list.append(char_code)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF=False, 
                                               ShowPositionF=False, EndStr=end_str,
                                               MarkerCharList=marker_char_list, LocalVariableDB=local_variable_db)

def create_range_skipper_code(Language, TestStr, EndSequence, QuexBufferSize=1024, 
                              CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(EndSequence) + 2

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    skipper_code, local_variable_db = range_skipper.get_skipper(EndSequence, OnSkipRangeOpenStr=end_str)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=local_variable_db) 

def create_nested_range_skipper_code(Language, TestStr, OpenSequence, CloseSequence, 
                                     QuexBufferSize=1024, CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloseSequence) + 2

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    skipper_code, local_variable_db = nested_range_skipper.get_skipper(OpenSequence, CloseSequence, 
                                                                       OnSkipRangeOpenStr=end_str)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=local_variable_db) 


def action(PatternName): 
    ##txt = 'fprintf(stderr, "%19s  \'%%s\'\\n", Lexeme);\n' % PatternName # DEBUG
    txt = 'printf("%19s  \'%%s\'\\n", Lexeme);\n' % PatternName

    if   "->1" in PatternName: txt += "me->current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);\n"
    elif "->2" in PatternName: txt += "me->current_analyzer_function = QUEX_NAME(Mrs_UnitTest_analyzer_function);\n"

    if "CONTINUE" in PatternName: txt += ""
    elif "STOP" in PatternName:   txt += "return false;"
    else:                         txt += "return true;"

    return txt
    
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
#ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue.i>
#endif


#if ! defined (__QUEX_OPTION_PLAIN_C)
    using namespace quex;
#endif

QUEX_NAMESPACE_MAIN_OPEN
QUEX_TYPE_CHARACTER        QUEX_NAME(LexemeNullObject);
static QUEX_TYPE_TOKEN_ID  QUEX_NAME_TOKEN(DumpedTokenIdObject) = (QUEX_TYPE_TOKEN_ID)0;
QUEX_NAMESPACE_MAIN_CLOSE


static           __QUEX_TYPE_ANALYZER_RETURN_VALUE  QUEX_NAME(Mr_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER*);
/* NOT static */ __QUEX_TYPE_ANALYZER_RETURN_VALUE  QUEX_NAME(Mrs_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER*);
/* Do not declare Mrs as 'static' otherwise there might be complaints if it
 * is never defined.                                                          */

static int
run_test(const char* TestString, const char* Comment, QUEX_TYPE_ANALYZER* lexer)
{
    lexer->current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);

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

def my_own_mr_unit_test_function(ShowPositionF, MarkerCharList, SourceCode, EndStr, LocalVariableDB={}):
    if ShowPositionF: show_position_str = "1"
    else:             show_position_str = "0"

    ml_txt = ""
    if MarkerCharList != []:
        for character in MarkerCharList:
            ml_txt += "        if( input == %i ) break;\n" % character
    else:
        ml_txt += "    break;\n"

    return blue_print(customized_unit_test_function_txt,
                      [("$$MARKER_LIST$$",     ml_txt),
                       ("$$SHOW_POSITION$$",   show_position_str),
                       ("$$LOCAL_VARIABLES$$", __local_variable_definitions(LocalVariableDB)),
                       ("$$SOURCE_CODE$$",     SourceCode),
                       ("$$END_STR$$",         EndStr)])


customized_unit_test_function_txt = """
bool
show_next_character(QUEX_NAME(Buffer)* buffer) {
    QUEX_TYPE_CHARACTER_POSITION* post_context_start_position = 0x0;
    QUEX_TYPE_CHARACTER_POSITION  last_acceptance_input_position = 0x0;

    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) == 0 ) {
        QUEX_NAME(Buffer_mark_lexeme_start)(buffer);
        if( QUEX_NAME(Buffer_is_end_of_file)(buffer) ) {
            return false;
        }
        QUEX_NAME(buffer_reload_forward_LA_PC)(buffer, &last_acceptance_input_position,
                                               post_context_start_position, 0);
        QUEX_NAME(Buffer_input_p_increment)(buffer);
    }
    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) != 0 ) {
#       if $$SHOW_POSITION$$
        printf("next letter: <%c> position: %04X\\n", (char)(*(buffer->_input_p)),
               (int)(buffer->_input_p - buffer->_memory._front));
#       else
        printf("next letter: <%c>\\n", (char)(*(buffer->_input_p)));
#       endif
    }
    return true;
}

__QUEX_TYPE_ANALYZER_RETURN_VALUE QUEX_NAME(Mr_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER* me)
{
#   define  engine (me)
    QUEX_TYPE_CHARACTER_POSITION* post_context_start_position    = 0x0;
    QUEX_TYPE_CHARACTER_POSITION  last_acceptance_input_position = 0x0;
    const size_t                  PostContextStartPositionN      = 0;
    QUEX_TYPE_CHARACTER           input                          = 0x0;
$$LOCAL_VARIABLES$$

ENTRY:
    /* Skip irrelevant characters */
    while(1 + 1 == 2) { 
        input = QUEX_NAME(Buffer_input_get)(&me->buffer);
$$MARKER_LIST$$
        if( QUEX_NAME(Buffer_distance_input_to_text_end)(&me->buffer) == 0 ) {
            QUEX_NAME(Buffer_mark_lexeme_start)(&me->buffer);
            if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {
                goto TERMINAL_END_OF_STREAM;
            }
            QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                                   post_context_start_position, 0);
        }
        QUEX_NAME(Buffer_input_p_increment)(&me->buffer);
    }
/*________________________________________________________________________________________*/
$$SOURCE_CODE$$
/*________________________________________________________________________________________*/

__REENTRY:
    /* Originally, the reentry preparation does not increment or do anything to _input_p
     * Here, we use the chance to print the position where the skipper ended.
     * If we are at the border and there is still stuff to load, then load it so we can
     * see what the next character is coming in.                                          */
    if( ! show_next_character(&me->buffer) ) goto TERMINAL_END_OF_STREAM; 
    goto ENTRY;

TERMINAL_END_OF_STREAM:
$$END_STR$$
#undef engine
}
"""

test_program_db = { 
    "ANSI-C-PlainMemory": """
    #include <stdlib.h>

    int main(int argc, char** argv)
    {
        TestAnalyzer         lexer_state;
        QUEX_TYPE_CHARACTER  TestString[] = "\\0$$TEST_STRING$$\\0";
        const size_t         MemorySize   = strlen((const char*)TestString+1) + 2;

        QUEX_NAME(construct_basic)(&lexer_state, (void*)0x0,
                                   TestString, MemorySize, TestString + MemorySize - 1, 
                                   0x0, 0, false);
        lexer_state.current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);
        QUEX_NAME(Buffer_end_of_file_set)(&lexer_state.buffer, TestString + MemorySize - 1);
        /**/
        return run_test((const char*)(TestString + 1), "$$COMMENT$$", &lexer_state);
    }\n""",

    "ANSI-C": """
    #include <stdio.h>
    /* #include <quex/code_base/buffer/plain/BufferFiller_Plain> */

    int main(int argc, char** argv)
    {
        TestAnalyzer      lexer_state;
        /**/
        const char*       test_string = "$$TEST_STRING$$";
        FILE*             fh          = tmpfile();

        /* Write test string into temporary file */
        fwrite(test_string, strlen(test_string), 1, fh);
        fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

        QUEX_NAME(construct_basic)(&lexer_state, fh, 0x0,
                                    $$BUFFER_SIZE$$, 0x0, 0x0,
                                    /* No translation, no translation buffer */0x0, false);
        /**/
        (void)run_test(test_string, "$$COMMENT$$", &lexer_state);

        fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
        return 0;
    }\n""",

    "Cpp": """
    #include <cstring>
    #include <sstream>
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>

    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        TestAnalyzer  lexer_state;
        /**/
        istringstream istr("$$TEST_STRING$$");

        QUEX_NAME(construct_basic)(&lexer_state, &istr, 0x0,
                                   $$BUFFER_SIZE$$, 0x0, 0x0, /* No translation, no translation buffer */0x0, false);

        return run_test("$$TEST_STRING$$", "$$COMMENT$$", &lexer_state);
    }\n""",

    "Cpp_StrangeStream": """
    #include <cstring>
    #include <sstream>
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>
    #include <quex/code_base/test_environment/StrangeStream>


    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        TestAnalyzer lexer_state;
        /**/
        istringstream                 istr("$$TEST_STRING$$");
        StrangeStream<istringstream>  strange_stream(&istr);

        QUEX_NAME(construct_basic)(&lexer_state, &strange_stream, 0x0,
                                    $$BUFFER_SIZE$$, 0x0, 0x0, /* No translation, no translation buffer */0x0, false);
        return run_test("$$TEST_STRING$$", "$$COMMENT$$", &lexer_state);
    }\n""",
}


