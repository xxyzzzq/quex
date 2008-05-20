#! /usr/bin/env python
import sys
import os
from StringIO import StringIO
from tempfile import mkstemp
sys.path.insert(0, os.environ["QUEX_PATH"])
#
from quex.frs_py.string_handling import blue_print
from quex.exception              import RegularExpressionException
from quex.lexer_mode             import PatternShorthand
#
from   quex.core_engine.generator.action_info   import ActionInfo
import quex.core_engine.generator.core          as generator
import quex.core_engine.regular_expression.core as regex

def action(PatternName): 
    # txt = 'fprintf(stderr, "%19s  \'%%s\'\\n", Lexeme);\n' % PatternName # DEBUG
    txt = 'printf("%19s  \'%%s\'\\n", Lexeme);\n' % PatternName

    if   "->1" in PatternName: txt += "me->__current_mode_analyser_function_p = analyser_do;\n"
    elif "->2" in PatternName: txt += "me->__current_mode_analyser_function_p = analyser_do_2;\n"

    if "CONTINUE" in PatternName: txt += ""
    elif "STOP" in PatternName:   txt += "return 0;"
    else:                         txt += "return 1;"

    return txt
    

test_program_common_declarations = """
struct QUEX_CORE_ANALYSER_STRUCT;
static int    analyser_do(QUEX_CORE_ANALYSER_STRUCT* me);
static int    analyser_do_2(QUEX_CORE_ANALYSER_STRUCT* me);
const int TKN_TERMINATION = 0;
"""

test_program_common = """
int main(int, char**)
{
    using namespace std;

    analyser   lexer_state;
    //
    int    success_f = 0;
    //
    $$BUFFER_SPECIFIC_SETUP$$
    //
    printf("(*) test string: \\n'$$TEST_STRING$$'\\n");
    printf("(*) result:\\n");
    do {
        success_f = lexer_state.__current_mode_analyser_function_p(&lexer_state);
    } while ( success_f );      
    printf("  ''\\n");
}\n"""

quex_buffer_based_test_program = """
    istringstream                                           istr("$$TEST_STRING$$");
    quex::fixed_size_character_stream_plain<istringstream, QUEX_CHARACTER_TYPE>  fscs(&istr);
    quex::buffer< QUEX_CHARACTER_TYPE>   buf(&fscs, $$BUFFER_SIZE$$, $$BUFFER_FALLBACK_N$$);

    analyser_init(&lexer_state, 0, &buf, analyser_do);
"""

plain_memory_based_test_program = """
    char   tmp[] = "\\0$$TEST_STRING$$";  // introduce first '0' for safe backward lexing

    analyser_init(&lexer_state, &(tmp[1]), analyser_do);
"""

def create_main_function(BufferType, TestStr, QuexBufferSize, QuexBufferFallbackN):
    global plain_memory_based_test_program
    global quex_buffer_based_test_program
    global test_program_common

    txt = test_program_common
    
    if BufferType=="QuexBuffer": 
        if QuexBufferFallbackN == -1: QuexBufferFallbackN = QuexBufferSize - 3
        include_str  = "#include <quex/code_base/buffer/plain/fixed_size_character_stream>\n"
        include_str += "#include <sstream>\n" 

        txt = include_str + txt

        buffer_specific_str = quex_buffer_based_test_program.replace("$$BUFFER_SIZE$$", repr(QuexBufferSize))
        buffer_specific_str = buffer_specific_str.replace("$$BUFFER_FALLBACK_N$$", repr(QuexBufferFallbackN))
        core_engine_definition_file = "quex/code_base/core_engine/definitions-quex-buffer.h"
    else:                        
        buffer_specific_str = plain_memory_based_test_program
        core_engine_definition_file = "quex/code_base/core_engine/definitions-plain-memory.h"

    test_str = TestStr.replace("\"", "\\\"")
    test_str = test_str.replace("\n", "\\n\"\n\"")

    txt = txt.replace("$$BUFFER_SPECIFIC_SETUP$$", buffer_specific_str)
    txt = txt.replace("$$TEST_STRING$$",           test_str)

    return txt, core_engine_definition_file


def create_state_machine_function(PatternActionPairList, PatternDictionary, 
                                  BufferLimitCode,
                                  core_engine_definition_file, SecondModeF=False):
    default_action = "return 0;"

    # -- produce some visible output about the setup
    print "(*) Lexical Analyser Patterns:"
    for pair in PatternActionPairList:
        print "%20s --> %s" % (pair[0], pair[1])
    # -- create default action that prints the name and the content of the token
    try:
        PatternActionPairList = map(lambda x: 
                                    ActionInfo(regex.do(x[0], PatternDictionary, 
                                                        BufferLimitCode), 
                                                        action(x[1])),
                                    PatternActionPairList)
    except RegularExpressionException, x:
        print "Regular expression parsing:\n" + x.message
        sys.exit(0)

    print "## (1) code generation"    
    txt  = "#include<cstdio>\n"
    txt += "#define  __QUEX_OPTION_UNIT_TEST\n"

    txt += generator.do(PatternActionPairList, 
                        DefaultAction                  = default_action, 
                        PrintStateMachineF             = True,
                        AnalyserStateClassName         = "analyser",
                        StandAloneAnalyserF            = True, 
                        QuexEngineHeaderDefinitionFile = core_engine_definition_file,
                        EndOfFile_Code                 = 0x19)

    if SecondModeF: txt = txt.replace("analyser_do(", "analyser_do_2(")

    return txt


def do(PatternActionPairList, TestStr, PatternDictionary={}, BufferType="PlainMemory", QuexBufferSize=15,
       SecondPatternActionPairList=[], QuexBufferFallbackN=-1, ShowBufferLoadsF=False,
       NDEBUG_str=""):    

    if BufferType=="QuexBuffer": BufferLimitCode = 0;
    else:                        BufferLimitCode = -1;

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
    
    test_program, core_engine_definition_file = create_main_function(BufferType, TestStr,
                                                                     QuexBufferSize, QuexBufferFallbackN)

    state_machine_code = create_state_machine_function(PatternActionPairList, 
                                                       adapted_dict, 
                                                       BufferLimitCode,
                                                       core_engine_definition_file)

    if SecondPatternActionPairList != []:
        state_machine_code += create_state_machine_function(SecondPatternActionPairList, 
                                                            PatternDictionary, 
                                                            BufferLimitCode,
                                                            core_engine_definition_file, 
                                                            SecondModeF=True)


    if ShowBufferLoadsF:
        state_machine_code = "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS\n" + \
                             "#define __QUEX_OPTION_UNIT_TEST\n" + \
                             "#define __QUEX_OPTION_UNIT_TEST_QUEX_BUFFER\n" + \
                             state_machine_code

    fd, filename_tmp = mkstemp(".cpp", "tmp-", dir=os.getcwd())
    os.write(fd, test_program_common_declarations)
    os.write(fd, state_machine_code)
    os.write(fd, test_program)    
    os.close(fd)    

    os.system("mv -f %s tmp.cpp" % filename_tmp); filename_tmp = "./tmp.cpp" # DEBUG

    print "## (2) compiling generated engine code and test"    
    compile_str = "g++ %s %s " % (NDEBUG_str, filename_tmp) + \
                  "-I./. -I$QUEX_PATH " + \
                  "-o %s.exe " % filename_tmp + \
                  "-D__QUEX_OPTION_UNIT_TEST_ISOLATED_CODE_GENERATION " + \
                  "-ggdb "# + \
                  #"-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS " + \
                  #"-D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS " 

    ## print compile_str # DEBUG
    os.system(compile_str)

    print "## (3) running the test"
    try:
        os.system("%s.exe" % filename_tmp)
        os.remove("%s.exe" % filename_tmp)
    except:
        print "<<compilation failed>>"
    print "## (4) cleaning up"
    # os.remove(filename_tmp)


