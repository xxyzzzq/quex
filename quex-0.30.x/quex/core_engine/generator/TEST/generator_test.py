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
from   quex.core_engine.generator.action_info   import ActionInfo
import quex.core_engine.generator.core          as generator
import quex.core_engine.regular_expression.core as regex

def action(PatternName): 
    ##txt = 'fprintf(stderr, "%19s  \'%%s\'\\n", Lexeme);\n' % PatternName # DEBUG
    txt = 'printf("%19s  \'%%s\'\\n", Lexeme);\n' % PatternName

    txt += "#ifndef __QUEX_SETTING_PLAIN_C\n"
    if   "->1" in PatternName: txt += "me->current_analyser_function = Mr_UnitTest_analyser_function<char>;\n"
    elif "->2" in PatternName: txt += "me->current_analyser_function = Mrs_UnitTest_analyser_function<char>;\n"
    txt += "#else\n"
    if   "->1" in PatternName: txt += "me->current_analyser_function = Mr_UnitTest_analyser_function;\n"
    elif "->2" in PatternName: txt += "me->current_analyser_function = Mrs_UnitTest_analyser_function;\n"
    txt += "#endif\n"

    if "CONTINUE" in PatternName: txt += ""
    elif "STOP" in PatternName:   txt += "return 0;"
    else:                         txt += "return 1;"

    return txt
    
test_program_common_declarations = """
const int TKN_TERMINATION = 0;
#define QUEX_SETTING_BUFFER_LIMIT_CODE ($$BUFFER_LIMIT_CODE$$)
typedef int QUEX_TOKEN_ID_TYPE;
#define __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
$$TEST_CASE$$
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/template/Analyser>
#if defined (__QUEX_SETTING_PLAIN_C)
    static __QUEX_SETTING_ANALYSER_FUNCTION_RETURN_TYPE  Mr_UnitTest_analyser_function(QuexAnalyser* me);
    static __QUEX_SETTING_ANALYSER_FUNCTION_RETURN_TYPE  Mrs_UnitTest_analyser_function(QuexAnalyser* me);
#else
    template<class CharacterCarrierType> inline
    __QUEX_SETTING_ANALYSER_FUNCTION_RETURN_TYPE  Mr_UnitTest_analyser_function(quex::QuexAnalyser<CharacterCarrierType>* me);
    template<class CharacterCarrierType> inline 
    __QUEX_SETTING_ANALYSER_FUNCTION_RETURN_TYPE  Mrs_UnitTest_analyser_function(quex::QuexAnalyser<CharacterCarrierType>* me);
#endif
"""

test_program_common = """

#include <cstring>
#include <quex/code_base/template/Analyser.i>

#if ! defined(__QUEX_SETTING_PLAIN_C)
    #include <quex/code_base/buffer/plain/BufferFiller_Plain>

    int main(int, char**)
    {
        using namespace std;
        using namespace quex;

        QuexAnalyser<char> lexer_state;
        int                       success_f = 0;
        //
        istringstream                                 istr("$$TEST_STRING$$");
        QuexBufferFiller_Plain<istringstream, char>   buffer_filler;
        const size_t                                  MemorySize = $$BUFFER_SIZE$$;

        BufferFiller_Plain_init(&buffer_filler, (size_t)$$BUFFER_FALLBACK_N$$, &istr);

        QuexAnalyser_init(&lexer_state, Mr_UnitTest_analyser_function<char>, 
                                 (char*)0x0, MemorySize, /* BLC */(char)0x0, 
                                 &buffer_filler.base);
        //
        printf("(*) test string: \\n'$$TEST_STRING$$'\\n");
        printf("(*) result:\\n");
        do {
            success_f = lexer_state.current_analyser_function(&lexer_state);
        } while ( success_f );      
        printf("  ''\\n");
    }
#else
    int main(int, char**)
    {
        using namespace std;

        QuexAnalyser   lexer_state;
        int                   success_f = 0;
        char                  tmp[] = "\\0$$TEST_STRING$$";  // introduce first '0' for safe backward lexing

        QuexAnalyser_init(&lexer_state, Mr_UnitTest_analyser_function, 
                                 (QUEX_CHARACTER_TYPE*)&tmp, strlen(tmp) + 1, /* BLC */0x0,
                                 /* buffer filler = */ 0x0);
        //
        printf("(*) test string: \\n'$$TEST_STRING$$'\\n");
        printf("(*) result:\\n");
        do {
            success_f = lexer_state.current_analyser_function(&lexer_state);
        } while ( success_f );      
        printf("  ''\\n");
    }
#endif
\n"""


def create_main_function(BufferType, TestStr, QuexBufferSize, QuexBufferFallbackN):
    global plain_memory_based_test_program
    global quex_buffer_based_test_program
    global test_program_common

    test_str = TestStr.replace("\"", "\\\"")
    test_str = test_str.replace("\n", "\\n\"\n\"")
    
    if BufferType=="QuexBuffer": 
        if QuexBufferFallbackN == -1: QuexBufferFallbackN = QuexBufferSize - 3
        # if QuexBufferFallbackN == -1: QuexBufferFallbackN = QuexBufferSize - 5
        include_str = "#include <sstream>\n" 

    else:                        
        include_str = ""

    txt = include_str + test_program_common
    txt = txt.replace("$$BUFFER_SIZE$$",       repr(QuexBufferSize))
    txt = txt.replace("$$BUFFER_FALLBACK_N$$", repr(QuexBufferFallbackN))
    txt = txt.replace("$$TEST_STRING$$",       test_str)

    return txt

def create_state_machine_function(PatternActionPairList, PatternDictionary, 
                                  BufferLimitCode,
                                  SecondModeF=False):
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

    if not SecondModeF:  sm_name = "Mr"
    else:                sm_name = "Mrs"

    txt += generator.do(PatternActionPairList, 
                        StateMachineName               = "UnitTest",
                        DefaultAction                  = default_action, 
                        PrintStateMachineF             = True,
                        AnalyserStateClassName         = sm_name,
                        StandAloneAnalyserF            = True, 
                        EndOfFile_Code                 = 0x19)

    return txt

def do(PatternActionPairList, TestStr, PatternDictionary={}, BufferType="PlainMemory", 
       QuexBufferSize=15, # DO NOT CHANGE!
       SecondPatternActionPairList=[], QuexBufferFallbackN=-1, ShowBufferLoadsF=False,
       NDEBUG_str=""):    

    if BufferType=="QuexBuffer": BufferLimitCode = 0;
    else:                        BufferLimitCode = 0;

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

    common_str = test_program_common_declarations
    common_str = common_str.replace("$$BUFFER_LIMIT_CODE$$", repr(BufferLimitCode))
    test_case_str = { "QuexBuffer":  "// #define __QUEX_SETTING_PLAIN_C",
                      "PlainMemory": "#define __QUEX_SETTING_PLAIN_C\n" + \
                                     "typedef unsigned char QUEX_CHARACTER_TYPE;\n", }[BufferType]
    common_str = common_str.replace("$$TEST_CASE$$", test_case_str)
    
    test_program = create_main_function(BufferType, TestStr,
                                        QuexBufferSize, QuexBufferFallbackN)

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

    fd, filename_tmp = mkstemp(".cpp", "tmp-", dir=os.getcwd())
    os.write(fd, common_str)
    os.write(fd, state_machine_code)
    os.write(fd, test_program) 
    os.close(fd)    

    os.system("mv -f %s tmp.cpp" % filename_tmp); filename_tmp = "./tmp.cpp" # DEBUG

    print "## (2) compiling generated engine code and test"    
    compile_str = "g++ %s %s " % (NDEBUG_str, filename_tmp) + \
                  "-I./. -I$QUEX_PATH " + \
                  "-o %s.exe " % filename_tmp + \
                  "-D__QUEX_OPTION_UNIT_TEST_ISOLATED_CODE_GENERATION " + \
                  "-DQUEX_OPTION_ACTIVATE_ASSERTS " + \
                  "-ggdb " + \
                  ""# "-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS " + \
                  #"-D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS " 

    print compile_str + "##" # DEBUG
    os.system(compile_str)
    sys.stdout.flush()

    print "## (3) running the test"
    try:
        fh_out = open(filename_tmp + ".out", "w")
        subprocess.call("./%s.exe" % filename_tmp, stdout=fh_out)
        fh_out.close()
        fh_out = open(filename_tmp + ".out", "r")
        print fh_out.read()
        os.remove("%s.exe" % filename_tmp)
    except:
        print "<<compilation failed>>"
    print "## (4) cleaning up"
    # os.remove(filename_tmp)


