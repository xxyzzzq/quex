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

SHOW_TRANSITIONS_STR  = "" # "-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS "  
SHOW_BUFFER_LOADS_STR = "" # "-D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS " 

def do(PatternActionPairList, TestStr, PatternDictionary={}, Language="ANSI-C-PlainMemory", 
       QuexBufferSize=15, # DO NOT CHANGE!
       SecondPatternActionPairList=[], QuexBufferFallbackN=-1, ShowBufferLoadsF=False,
       AssertsActionvation_str="-DQUEX_OPTION_ASSERTS"):    

    BufferLimitCode = 0

    try:
        adapted_dict = {}
        for key, regular_expression in PatternDictionary.items():
            string_stream = StringIO(regular_expression)
            state_machine = regex.do(string_stream, adapted_dict, 
                                     BufferLimitCode  = BufferLimitCode)
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

    compile_and_run(Language, source_code, AssertsActionvation_str)

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
            if line.find("defined but not used") != -1:
                postponed_list.append("## IGNORED: " + line.replace(os.environ["QUEX_PATH"] + "/quex/", ""))
            else:
                print line
        for line in postponed_list:
            print line
        os.remove("tmp.out")
        os.remove("tmp.err")
    except:
        print "<<execution failed>>"

def compile_and_run(Language, SourceCode, AssertsActionvation_str=""):
    print "## (*) compiling generated engine code and test"    
    if Language in ["ANSI-C", "ANSI-C-PlainMemory"]:
        extension = ".c"
        # The '-Wvariadic-macros' shall remind us that we do not want use variadic macroes.
        # Because, some compilers do not swallow them!
        compiler  = "gcc -ansi -Wvariadic-macros -Wall"
    else:
        extension = ".cpp"
        compiler  = "g++ -Wall"

    if Language.find("StrangeStream") != -1:
        compiler += " -DQUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION "


    fd, filename_tmp = mkstemp(extension, "tmp-", dir=os.getcwd())
    os.write(fd, SourceCode) 
    os.close(fd)    
    
    os.system("mv -f %s tmp%s" % (filename_tmp, extension)); filename_tmp = "./tmp%s" % extension # DEBUG

    # NOTE: QUEX_OPTION_ASSERTS is defined by AssertsActionvation_str (or not)
    compile_str = compiler + " %s %s " % (AssertsActionvation_str, filename_tmp) + \
                  "-I./. -I%s " % os.environ["QUEX_PATH"] + \
                  "-o %s.exe " % filename_tmp + \
                  "-ggdb " + \
                  SHOW_TRANSITIONS_STR + " " + \
                  SHOW_BUFFER_LOADS_STR

    print compile_str + "##" # DEBUG
    run_this(compile_str)
    sys.stdout.flush()

    print "## (*) running the test"
    run_this("./%s.exe" % filename_tmp)
    os.remove("%s.exe" % filename_tmp)
    #os.remove(filename_tmp)

def create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF=False):
    global plain_memory_based_test_program
    global quex_buffer_based_test_program
    global test_program_common

    test_str = TestStr.replace("\"", "\\\"")
    test_str = test_str.replace("\n", "\\n\"\n\"")
    
    txt = test_program_db[Language]
    txt = txt.replace("$$BUFFER_SIZE$$",       repr(QuexBufferSize))
    txt = txt.replace("$$TEST_STRING$$",       test_str)
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
    txt = txt.replace("$$BUFFER_LIMIT_CODE$$", repr(BufferLimitCode))

    if Language in ["ANSI-C", "ANSI-C-PlainMemory"]:
        test_case_str = "#define __QUEX_SETTING_PLAIN_C\n" + \
                        "typedef unsigned char QUEX_TYPE_CHARACTER;\n"
    else:
        test_case_str = "/* #define __QUEX_SETTING_PLAIN_C */\n" + \
                        "typedef unsigned char QUEX_TYPE_CHARACTER;\n"

    return txt.replace("$$TEST_CASE$$", test_case_str)

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
                                    PatternActionInfo(regex.do(x[0], PatternDictionary, BufferLimitCode), 
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
                        StateMachineName       = "UnitTest",
                        OnFailureAction        = PatternActionInfo(None, on_failure_action), 
                        EndOfStreamAction      = PatternActionInfo(None, on_failure_action), 
                        PrintStateMachineF     = True,
                        AnalyserStateClassName = sm_name,
                        StandAloneAnalyserF    = True)

    return generator.delete_unused_labels(txt)

def __get_skipper_code_framework(Language, TestStr, SkipperSourceCode, 
                                 QuexBufferSize, CommentTestStrF, ShowPositionF, EndStr, MarkerCharList):

    txt  = "#define QUEX_TYPE_CHARACTER uint8_t\n"
    txt += "#define QUEX_TYPE_TOKEN_XXX_ID  bool\n"  
    txt += "typedef void QUEX_NAME(Mode);\n"
    if Language.find("Cpp") == -1: txt += "#define __QUEX_SETTING_PLAIN_C\n"
    txt += "#define QUEX_NAME(AnalyzerData)     QuexAnalyzerEngine\n"
    txt += "#define QUEX_NAME(AnalyzerData_tag) QuexAnalyzerEngine_tag\n"
    txt += "#define QUEX_TYPE_ANALYZER          QuexAnalyzerEngine\n"
    txt += "#define QUEX_TYPE_ANALYZER_TAG      QuexAnalyzerEngine_tag\n"
    txt += "#include <quex/code_base/analyzer/configuration/default>\n"
    txt += "#ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION\n"
    txt += "#   include <quex/code_base/test_environment/StrangeStream>\n"
    txt += "#endif\n"
    txt += "#include <quex/code_base/analyzer/Engine>\n"
    txt += "#include <quex/code_base/analyzer/Engine.i>\n"
    txt += "\n"
    if Language.find("Cpp") != -1: txt += "using namespace quex;\n"
    txt += "\n"
    txt += "bool analyzis_terminated_f = false;\n"
    txt += "\n"
    txt += "bool\n"
    txt += "show_next_character(QuexBuffer* buffer) {\n"
    txt += "    QUEX_TYPE_CHARACTER_POSITION* post_context_start_position = 0x0;\n"
    txt += "    QUEX_TYPE_CHARACTER_POSITION  last_acceptance_input_position = 0x0;\n"
    txt += "    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) == 0 ) {\n"
    txt += "        QUEX_NAME(Buffer_mark_lexeme_start)(buffer);\n"
    txt += "        if( QUEX_NAME(Engine_buffer_reload_forward)(buffer, &last_acceptance_input_position,\n"
    txt += "                                                    post_context_start_position, 0) == 0 ) {\n"
    txt += "            return false;\n"
    txt += "        } else {\n"
    txt += "            QUEX_NAME(Buffer_input_p_increment)(buffer);\n"
    txt += "        }\n"
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
    txt += "void Mr_UnitTest_analyzer_function(QUEX_NAME(AnalyzerData)* me)\n"
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
    txt += "            if( QUEX_NAME(Engine_buffer_reload_forward)(&me->buffer, &last_acceptance_input_position,\n"
    txt += "                                                   post_context_start_position, 0) == 0 )\n"
    txt += "                goto TERMINAL_END_OF_STREAM;\n"
    txt += "            QUEX_NAME(Buffer_input_p_increment)(&me->buffer);\n"
    txt += "        } else {\n"
    txt += "            QUEX_NAME(Buffer_input_p_increment)(&me->buffer);\n"
    txt += "        }\n"
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

    if   "->1" in PatternName: txt += "me->current_analyzer_function = Mr_UnitTest_analyzer_function;\n"
    elif "->2" in PatternName: txt += "me->current_analyzer_function = Mrs_UnitTest_analyzer_function;\n"

    if "CONTINUE" in PatternName: txt += ""
    elif "STOP" in PatternName:   txt += "analyzis_terminated_f = true; return;"
    else:                         txt += "return;"

    return txt
    
test_program_common_declarations = """
const int TKN_TERMINATION = 0;
#define QUEX_SETTING_BUFFER_LIMIT_CODE      ((QUEX_TYPE_CHARACTER)$$BUFFER_LIMIT_CODE$$)
typedef int QUEX_TYPE_TOKEN_XXX_ID;              
typedef void QUEX_NAME(Mode);              
/* #define QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN */
#define QUEX_SETTING_BUFFER_MIN_FALLBACK_N  ((size_t)$$BUFFER_FALLBACK_N$$)
#define __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
#define __QUEX_OPTION_PLAIN_ANALYZER_OBJECT
$$TEST_CASE$$
#define QUEX_NAME(AnalyzerData)     QuexAnalyzerEngine
#define QUEX_NAME(AnalyzerData_tag) QuexAnalyzerEngine_tag
#define QUEX_TYPE_ANALYZER          QuexAnalyzerEngine
#define QUEX_TYPE_ANALYZER_TAG      QuexAnalyzerEngine_tag
#include <quex/code_base/analyzer/configuration/default>
#ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION 
#   include <quex/code_base/test_environment/StrangeStream>
#endif
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/analyzer/Engine>
#include <quex/code_base/analyzer/Engine.i>
#if ! defined (__QUEX_SETTING_PLAIN_C)
    using namespace quex;
#endif

bool analyzis_terminated_f = false;

static void  Mr_UnitTest_analyzer_function(struct QUEX_NAME(AnalyzerData_tag)*);
/* Do not declare Mrs as 'static' otherwise there might be complaints if it
 * is never defined.                                                          */
void  Mrs_UnitTest_analyzer_function(struct QUEX_NAME(AnalyzerData_tag)*);
"""

test_program_db = { 
    "ANSI-C-PlainMemory": """
    #include <stdlib.h>
    #include <quex/code_base/analyzer/Engine.i>

    int main(int argc, char** argv)
    {
        QuexAnalyzerEngine   lexer_state;
        QUEX_TYPE_CHARACTER  TestString[] = "\\0$$TEST_STRING$$\\0";
        const size_t         MemorySize   = strlen((const char*)TestString+1) + 2;

        QUEX_NAME(Engine_construct)(&lexer_state, Mr_UnitTest_analyzer_function, (void*)0x0,
                               TestString, MemorySize, 0x0, 0, false);
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
    #include <quex/code_base/analyzer/Engine.i>
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>

    int main(int argc, char** argv)
    {
        QuexAnalyzerEngine lexer_state;
        /**/
        const char*             test_string = "$$TEST_STRING$$";
        FILE*                   fh          = tmpfile();

        /* Write test string into temporary file */
        fwrite(test_string, strlen(test_string), 1, fh);
        fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

        QuexAnalyzerEngine_construct(&lexer_state, Mr_UnitTest_analyzer_function, fh, 0x0,
                               $$BUFFER_SIZE$$, 0x0, /* No translation, no translation buffer */0x0, false);
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
    #include <quex/code_base/analyzer/Engine.i>
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>

    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        QuexAnalyzerEngine lexer_state;
        /**/
        istringstream  istr("$$TEST_STRING$$");

        QUEX_NAME(Engine_construct)(&lexer_state, Mr_UnitTest_analyzer_function, &istr, 0x0,
                                    $$BUFFER_SIZE$$, 0x0, /* No translation, no translation buffer */0x0, false);
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
    #include <quex/code_base/analyzer/Engine.i>
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>

    int main(int argc, char** argv)
    {
        using namespace std;
        using namespace quex;

        QuexAnalyzerEngine lexer_state;
        /**/
        istringstream                 istr("$$TEST_STRING$$");
        StrangeStream<istringstream>  strange_stream(&istr);

        QUEX_NAME(Engine_construct)(&lexer_state, Mr_UnitTest_analyzer_function, &strange_stream, 0x0,
                                    $$BUFFER_SIZE$$, 0x0, /* No translation, no translation buffer */0x0, false);
        /**/
        printf("(*) test string: \\n'$$TEST_STRING$$'$$COMMENT$$\\n");
        printf("(*) result:\\n");
        for(analyzis_terminated_f = false; ! analyzis_terminated_f; )
            lexer_state.current_analyzer_function(&lexer_state);
        printf("  ''\\n");
        return 0;
    }\n""",
}


