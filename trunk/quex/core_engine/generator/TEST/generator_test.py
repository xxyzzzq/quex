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
from   quex.core_engine.generator.action_info    import PatternActionInfo, CodeFragment
import quex.core_engine.generator.core                     as generator
import quex.core_engine.generator.state_coder.skipper_core as skipper
import quex.core_engine.regular_expression.core            as regex
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


choices_list = ["ANSI-C-PlainMemory", "ANSI-C", "Cpp", "Cpp_StrangeStream", "Cpp-Template", "Cpp-Path", "Cpp-PathUniform", "Cpp-Path-CG"] 

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

def do(PatternActionPairList, TestStr, PatternDictionary={}, Language="ANSI-C-PlainMemory", 
       QuexBufferSize=15, # DO NOT CHANGE!
       SecondPatternActionPairList=[], QuexBufferFallbackN=-1, ShowBufferLoadsF=False,
       AssertsActionvation_str="-DQUEX_OPTION_ASSERTS"):

    BufferLimitCode = 0
    Setup.buffer_limit_code = BufferLimitCode

    CompileOptionStr = ""
    if Language.find("StrangeStream") != -1:
        CompileOptionStr += " -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION "

    if Language.find("-CG") != -1:
        Language = Language.replace("-CG", "")
        CompileOptionStr += " -D__QUEX_OPTION_USE_COMPUTED_GOTOS "

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
                             "#define __QUEX_OPTION_UNIT_TEST\n" + \
                             "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER\n" + \
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
               or     (line.find("warning: unused variable") != -1 )          \
                  and (line.find("path_") != -1 or line.find("pathwalker_") != -1) \
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

    # NOTE: QUEX_OPTION_ASSERTS is defined by AssertsActionvation_str (or not)
    compile_str = compiler                + " " + \
                  StrangeStream_str       + " " + \
                  AssertsActionvation_str + " " + \
                  filename_tmp            + " " + \
                  "-I./. -I%s " % os.environ["QUEX_PATH"] + \
                  "-o %s.exe " % filename_tmp             + \
                  "-ggdb"                 + " " + \
                  SHOW_TRANSITIONS_STR    + " " + \
                  SHOW_BUFFER_LOADS_STR

    print compile_str + "##" # DEBUG
    run_this(compile_str)
    sys.stdout.flush()

    print "## (*) running the test"
    run_this("./%s.exe" % filename_tmp)
    if REMOVE_FILES:
        os.remove("%s.exe" % filename_tmp)
        os.remove(filename_tmp)

def create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF=False):
    global plain_memory_based_test_program
    global quex_buffer_based_test_program
    global test_program_common

    test_str = TestStr.replace("\"", "\\\"")
    test_str = test_str.replace("\n", "\\n\"\n\"")
    
    txt = test_program_db[Language]
    txt = txt.replace("$$BUFFER_SIZE$$", repr(QuexBufferSize))
    txt = txt.replace("$$TEST_STRING$$", test_str)
    if CommentTestStrF: txt = txt.replace("$$COMMENT$$", "##")
    else:               txt = txt.replace("$$COMMENT$$", "")

    return txt

def create_common_declarations(Language, QuexBufferSize, TestStr, QuexBufferFallbackN=-1, BufferLimitCode=0):
    # Determine the 'fallback' region size in the buffer
    if QuexBufferFallbackN == -1: 
        QuexBufferFallbackN = QuexBufferSize - 3
    if Language == "ANSI-C-PlainMemory": 
        QuexBufferFallbackN = max(0, len(TestStr) - 3) 

    # Parameterize the common declarations
    txt = test_program_common_declarations.replace("$$BUFFER_FALLBACK_N$$", repr(QuexBufferFallbackN))
    txt = "#define QUEX_TYPE_CHARACTER unsigned char\n" + txt
    txt = txt.replace("$$BUFFER_LIMIT_CODE$$", repr(BufferLimitCode))

    if Language in ["ANSI-C", "ANSI-C-PlainMemory"]:
        txt = txt.replace("$$__QUEX_OPTION_PLAIN_C$$", "#define __QUEX_OPTION_PLAIN_C\n")
    else:
        txt = txt.replace("$$__QUEX_OPTION_PLAIN_C$$", "//#define __QUEX_OPTION_PLAIN_C\n")

    return txt

def create_state_machine_function(PatternActionPairList, PatternDictionary, 
                                  BufferLimitCode, SecondModeF=False):
    on_failure_action = "analyzis_terminated_f = true; return;"

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
                        StandAloneAnalyserF    = True)

    return generator.delete_unused_labels(txt)

def __get_skipper_code_framework(Language, TestStr, SkipperSourceCode, 
                                 QuexBufferSize, CommentTestStrF, ShowPositionF, EndStr, MarkerCharList):

    txt  = "#define QUEX_TYPE_CHARACTER uint8_t\n"
    if Language.find("Cpp") == -1: txt += "#define __QUEX_OPTION_PLAIN_C\n"
    txt += "#include <quex/code_base/analyzer/configuration/default>\n"
    txt += "#if ! defined (__QUEX_OPTION_PLAIN_C)\n"
    txt += "    namespace quex {\n"
    txt += "#endif\n"
    txt += "typedef struct {} QUEX_TYPE_TOKEN_WITHOUT_NAMESPACE;\n"
    txt += "void QUEX_NAME_TOKEN(construct)(QUEX_TYPE_TOKEN* me) {}\n"
    txt += "void QUEX_NAME_TOKEN(destruct)(QUEX_TYPE_TOKEN* me) {}\n"
    txt += "#if ! defined (__QUEX_OPTION_PLAIN_C)\n"
    txt += "    }\n"
    txt += "#endif\n"
    txt += "#ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION\n"
    txt += "#   include <quex/code_base/test_environment/StrangeStream>\n"
    txt += "#endif\n"
    txt += "#include <quex/code_base/buffer/Buffer>\n"
    txt += "#include <quex/code_base/buffer/Buffer.i>\n"
    txt += "#include <quex/code_base/buffer/BufferFiller.i>\n"
    txt += "#include <quex/code_base/test_environment/TestAnalyzer>\n"
    txt += "#include <quex/code_base/token/TokenQueue>\n"
    txt += "#include <quex/code_base/token/TokenQueue.i>\n"
    txt += "#include <quex/code_base/analyzer/member/basic.i>\n"
    txt += "\n"
    if Language.find("Cpp") != -1: txt += "using namespace quex;\n"
    txt += "\n"
    txt += "bool analyzis_terminated_f = false;\n"
    txt += "static QUEX_TYPE_TOKEN_ID __QuexDumpedTokenIdObject = 0;\n"
    txt += "\n"
    txt += "bool\n"
    txt += "show_next_character(QUEX_NAME(Buffer)* buffer) {\n"
    txt += "    QUEX_TYPE_CHARACTER_POSITION* post_context_start_position = 0x0;\n"
    txt += "    QUEX_TYPE_CHARACTER_POSITION  last_acceptance_input_position = 0x0;\n"
    txt += "    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) == 0 ) {\n"
    txt += "        QUEX_NAME(Buffer_mark_lexeme_start)(buffer);\n"
    txt += "        if( QUEX_NAME(Buffer_is_end_of_file)(buffer) ) {\n"
    txt += "            return false;"
    txt += "        }\n"
    txt += "        QUEX_NAME(buffer_reload_forward_LA_PC)(buffer, &last_acceptance_input_position,\n"
    txt += "                                               post_context_start_position, 0);\n"
    txt += "        QUEX_NAME(Buffer_input_p_increment)(buffer);\n"
    txt += "    }\n"
    txt += "    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) != 0 )\n"
    if ShowPositionF:
        txt += '    printf("next letter: <%c> position: %04X\\n", (char)(*(buffer->_input_p)),\n'
        txt += '           (int)(buffer->_input_p - buffer->_memory._front));\n'
    else:
        txt += '    printf("next letter: <%c>\\n", (char)(*(buffer->_input_p)));\n'
    txt += "    return true;\n"
    txt += "}\n"
    txt += "\n"
    txt += "void QUEX_NAME(Mr_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER* me)\n"
    txt += "{\n"
    txt += "#   define  engine (me)\n"
    txt += "    QUEX_TYPE_CHARACTER_POSITION* post_context_start_position    = 0x0;\n"
    txt += "    QUEX_TYPE_CHARACTER_POSITION  last_acceptance_input_position = 0x0;\n"
    txt += "    const size_t                  PostContextStartPositionN      = 0;\n"
    txt += "    QUEX_TYPE_CHARACTER           input                          = 0x0;\n"
    txt += "ENTRY:\n"
    txt += "    /* Skip irrelevant characters */\n"
    txt += "    while(1 + 1 == 2) {\n" 
    txt += "        input = QUEX_NAME(Buffer_input_get)(&me->buffer);\n"
    if MarkerCharList != []:
        for character in MarkerCharList:
            txt += "        if( input == %i ) break;\n" % character
    else:
        txt += "    break;\n"
    txt += "        if( QUEX_NAME(Buffer_distance_input_to_text_end)(&me->buffer) == 0 ) {\n"
    txt += "            QUEX_NAME(Buffer_mark_lexeme_start)(&me->buffer);\n"
    txt += "            if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {\n"
    txt += "                goto TERMINAL_END_OF_STREAM;\n"
    txt += "            }\n"
    txt += "            QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,\n"
    txt += "                                                   post_context_start_position, 0);\n"
    txt += "        }\n"
    txt += "        QUEX_NAME(Buffer_input_p_increment)(&me->buffer);\n"
    txt += "    }\n"
    txt += "\n"
    txt += SkipperSourceCode
    txt += "\n"
    txt += "__REENTRY:\n"
    txt += "    /* Originally, the reentry preparation does not increment or do anything to _input_p\n"
    txt += "     * Here, we use the chance to print the position where the skipper ended.\n"
    txt += "     * If we are at the border and there is still stuff to load, then load it so we can\n"
    txt += "     * see what the next character is coming in.                                          */"
    txt += "    if( ! show_next_character(&me->buffer) ) goto TERMINAL_END_OF_STREAM;\n" 
    txt += "    goto ENTRY;\n"
    txt += "\n"
    txt += "TERMINAL_END_OF_STREAM:\n"
    txt += EndStr
    txt += "#undef engine\n"
    txt += "}\n"
    txt += "\n"
    txt += create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF)

    return txt

def create_character_set_skipper_code(Language, TestStr, TriggerSet, QuexBufferSize=1024):

    end_str  = '    printf("end\\n");'
    end_str += '    analyzis_terminated_f = true; return;\n'

    skipper_code = skipper.get_character_set_skipper(TriggerSet, db["C++"])

    marker_char_list = []
    for interval in TriggerSet.get_intervals():
        for char_code in range(interval.begin, interval.end):
            marker_char_list.append(char_code)
    return __get_skipper_code_framework(Language, TestStr, skipper_code,
                                        QuexBufferSize, CommentTestStrF=False, ShowPositionF=False, EndStr=end_str,
                                        MarkerCharList=marker_char_list)

def create_skipper_code(Language, TestStr, EndSequence, QuexBufferSize=1024, CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(EndSequence) + 2

    end_str  = '    printf("end\\n");'
    end_str += '    analyzis_terminated_f = true; return;\n'

    skipper_code = skipper.get_range_skipper(EndSequence, db["C++"], end_str)

    return __get_skipper_code_framework(Language, TestStr, skipper_code,
                                        QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                        MarkerCharList=[]) # [EndSequence[0]])


def action(PatternName): 
    ##txt = 'fprintf(stderr, "%19s  \'%%s\'\\n", Lexeme);\n' % PatternName # DEBUG
    txt = 'printf("%19s  \'%%s\'\\n", Lexeme);\n' % PatternName

    if   "->1" in PatternName: txt += "me->current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);\n"
    elif "->2" in PatternName: txt += "me->current_analyzer_function = QUEX_NAME(Mrs_UnitTest_analyzer_function);\n"

    if "CONTINUE" in PatternName: txt += ""
    elif "STOP" in PatternName:   txt += "analyzis_terminated_f = true; return;"
    else:                         txt += "return;"

    return txt
    
test_program_common_declarations = """
const int TKN_TERMINATION = 0;
#define QUEX_SETTING_BUFFER_MIN_FALLBACK_N  ((size_t)$$BUFFER_FALLBACK_N$$)
$$__QUEX_OPTION_PLAIN_C$$
#define __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
#define __QUEX_OPTION_PLAIN_ANALYZER_OBJECT
#define QUEX_SETTING_BUFFER_LIMIT_CODE      ((QUEX_TYPE_CHARACTER)$$BUFFER_LIMIT_CODE$$)
#include <quex/code_base/analyzer/configuration/default>
#if ! defined (__QUEX_OPTION_PLAIN_C)
    namespace quex {
#endif
typedef struct {} QUEX_TYPE_TOKEN_WITHOUT_NAMESPACE;
void QUEX_NAME_TOKEN(construct)(QUEX_TYPE_TOKEN* me) {}
void QUEX_NAME_TOKEN(destruct)(QUEX_TYPE_TOKEN* me) {}
#if ! defined (__QUEX_OPTION_PLAIN_C)
    }
#endif
/* #define QUEX_OPTION_TOKEN_POLICY_SINGLE */
#ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION 
#   include <quex/code_base/test_environment/StrangeStream>
#endif
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/MemoryManager.i>
#include <quex/code_base/test_environment/TestAnalyzer>
#include <quex/code_base/token/TokenQueue>
#include <quex/code_base/token/TokenQueue.i>
#include <quex/code_base/analyzer/member/basic.i>
#if ! defined (__QUEX_OPTION_PLAIN_C)
    using namespace quex;
#endif

static QUEX_TYPE_TOKEN_ID __QuexDumpedTokenIdObject = 0;

bool analyzis_terminated_f = false;

static           void  QUEX_NAME(Mr_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER*);
/* NOT static */ void  QUEX_NAME(Mrs_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER*);
/* Do not declare Mrs as 'static' otherwise there might be complaints if it
 * is never defined.                                                          */
"""

test_program_db = { 
    "ANSI-C-PlainMemory": """
    #include <stdlib.h>

    int main(int argc, char** argv)
    {
        QUEX_NAME(TestAnalyzer)   lexer_state;
        QUEX_TYPE_CHARACTER  TestString[] = "\\0$$TEST_STRING$$\\0";
        const size_t         MemorySize   = strlen((const char*)TestString+1) + 2;

        QUEX_NAME(construct_basic)(&lexer_state, (void*)0x0,
                                   TestString, MemorySize, 0x0, 0, false);
        lexer_state.current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);
        QUEX_NAME(Buffer_end_of_file_set)(&lexer_state.buffer, TestString + MemorySize - 1);
        /**/
        printf("(*) test string: \\n'%s'$$COMMENT$$\\n", TestString + 1);
        printf("(*) result:\\n");
        for(analyzis_terminated_f = false; ! analyzis_terminated_f; )
            lexer_state.current_analyzer_function(&lexer_state);
        printf("  ''\\n");
        return 0;
    }\n""",

    "ANSI-C": """
    #include <stdio.h>
    /* #include <quex/code_base/buffer/plain/BufferFiller_Plain> */

    int main(int argc, char** argv)
    {
        QUEX_NAME(TestAnalyzer) lexer_state;
        /**/
        const char*       test_string = "$$TEST_STRING$$";
        FILE*             fh          = tmpfile();

        /* Write test string into temporary file */
        fwrite(test_string, strlen(test_string), 1, fh);
        fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

        QUEX_NAME(construct_basic)(&lexer_state, fh, 0x0,
                                    $$BUFFER_SIZE$$, 0x0, 
                                    /* No translation, no translation buffer */0x0, false);
        lexer_state.current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);
        /**/
        printf("(*) test string: \\n'$$TEST_STRING$$'$$COMMENT$$\\n");
        printf("(*) result:\\n");
        for(analyzis_terminated_f = false; ! analyzis_terminated_f; )
            lexer_state.current_analyzer_function(&lexer_state);
        printf("  ''\\n");

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

        QUEX_NAME(TestAnalyzer)  lexer_state;
        /**/
        istringstream      istr("$$TEST_STRING$$");

        QUEX_NAME(construct_basic)(&lexer_state, &istr, 0x0,
                                   $$BUFFER_SIZE$$, 0x0, /* No translation, no translation buffer */0x0, false);

        lexer_state.current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);
        /**/
        printf("(*) test string: \\n'$$TEST_STRING$$'$$COMMENT$$\\n");
        printf("(*) result:\\n");
        for(analyzis_terminated_f = false; ! analyzis_terminated_f; )
            lexer_state.current_analyzer_function(&lexer_state);
        printf("  ''\\n");
        return 0;
    }\n""",

    "Cpp_StrangeStream": """
    #include <cstring>
    #include <sstream>
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>

    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        QUEX_NAME(TestAnalyzer) lexer_state;
        /**/
        istringstream                 istr("$$TEST_STRING$$");
        StrangeStream<istringstream>  strange_stream(&istr);

        QUEX_NAME(construct_basic)(&lexer_state, &strange_stream, 0x0,
                                    $$BUFFER_SIZE$$, 0x0, /* No translation, no translation buffer */0x0, false);
        lexer_state.current_analyzer_function = QUEX_NAME(Mr_UnitTest_analyzer_function);
        /**/
        printf("(*) test string: \\n'$$TEST_STRING$$'$$COMMENT$$\\n");
        printf("(*) result:\\n");
        for(analyzis_terminated_f = false; ! analyzis_terminated_f; )
            lexer_state.current_analyzer_function(&lexer_state);
        printf("  ''\\n");
        return 0;
    }\n""",
}


