#include <cstdio>
#include <cstdlib>
#include <cstring>
#define  QUEX_TYPE_CHARACTER            char
#define  QUEX_TKN_UNINITIALIZED         1
#define  QUEX_OPTION_TOKEN_POLICY_QUEUE
#define  QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE       0
#define  QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR 1
#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#ifdef     QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#   undef  QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#   define QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN_DISABLED
#else
#   define QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#   undef  QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN_DISABLED
#endif
#undef   QUEX_OPTION_INCLUDE_STACK
#define  QUEX_OPTION_STRING_ACCUMULATOR
#include <quex/code_base/converter_helper/from-unicode-buffer>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>
#include <quex/code_base/aux-string.i>
#include <quex/code_base/definitions>

QUEX_NAMESPACE_MAIN_OPEN
class TestAnalyzer;
QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/analyzer/Counter>
#include <quex/code_base/analyzer/Accumulator>

#if ! defined(QUEX_OPTION_MULTI)
#   define  QUEX_OPTION_MULTI_ALLOW_IMPLEMENTATION
#   include <quex/code_base/Multi.i>
#   undef   QUEX_OPTION_MULTI_ALLOW_IMPLEMENTATION
#endif

QUEX_NAMESPACE_LEXEME_NULL_OPEN
QUEX_TYPE_CHARACTER  QUEX_LEXEME_NULL_IN_ITS_NAMESPACE = (QUEX_TYPE_CHARACTER)0;
QUEX_NAMESPACE_LEXEME_NULL_CLOSE

QUEX_NAMESPACE_MAIN_OPEN

//#define QUEX_TOKEN_POLICY_SET_ID()       /* empty */
//#define QUEX_TOKEN_POLICY_PREPARE_NEXT() /* empty */

typedef struct { QUEX_TYPE_TOKEN_ID _id; } Token;

class TestAnalyzer {
public:
    struct { 
        QUEX_TYPE_TOKEN   begin[1];
        QUEX_TYPE_TOKEN*  write_iterator;
        QUEX_TYPE_TOKEN*  read_iterator;
        QUEX_TYPE_TOKEN*  memory_end;
    } _token_queue;

    QUEX_NAME(Counter)     counter;

    QUEX_NAME(Accumulator) accumulator;
};

bool 
QUEX_NAME_TOKEN(take_text)(QUEX_TYPE_TOKEN*           __this, 
                           QUEX_TYPE_ANALYZER*        analyzer, 
                           const QUEX_TYPE_CHARACTER* Begin, 
                           const QUEX_TYPE_CHARACTER* End)
{
    printf("Lexical Analyzer Receives:\n");
    printf("   '%s'\n", Begin);
    return true;
}

QUEX_NAMESPACE_MAIN_CLOSE

// Prevent the inclusion of 'token-sending.i' since we do it on our own.
//#define  __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING
//#define  __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I
//#define  __INCLUDE_INDICATOR_QUEX__TOKEN_POLICY__
#include <quex/code_base/analyzer/C-adaptions.h>
#include <quex/code_base/analyzer/Accumulator.i>
#include <quex/code_base/analyzer/Counter.i>

int
main(int argc, char** argv)
{
    using namespace quex;

    char  TestString0[] = "AsSalaamu Alaikum";

    /* Ensure some settings that cause the accumulator to extend its memory */
    __quex_assert(QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE == 0);
    __quex_assert(QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR == 1);

    if( argc < 2 ) return -1;

    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Accumulator;\n");
        printf("CHOICES: String, Character, N-Character, N-String, Mix;\n");
        return 0;
    }
    TestAnalyzer            analyzer;
    QUEX_NAME(Accumulator)& accumulator = analyzer.accumulator;

#   define self analyzer

    analyzer._token_queue.write_iterator = analyzer._token_queue.begin;
    analyzer._token_queue.read_iterator = analyzer._token_queue.begin;
    QUEX_NAME(Accumulator_construct)(&accumulator, &analyzer);

    if     ( strcmp(argv[1], "String") == 0 ) {
        QUEX_NAME(Accumulator_add)(&accumulator, TestString0, TestString0 + strlen(TestString0));
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }
    else if( strcmp(argv[1], "Character") == 0 ) {
        QUEX_NAME(Accumulator_add_character)(&accumulator, 'a');
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }
    else if( strcmp(argv[1], "N-Character") == 0 ) {
        for(int i = 0; i != 104; ++i) 
            QUEX_NAME(Accumulator_add_character)(&accumulator, i % 26 + 'a');
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }
    else if( strcmp(argv[1], "N-String") == 0 ) {
        for(int i = 0; i != 10; ++i) 
            QUEX_NAME(Accumulator_add)(&accumulator, TestString0, TestString0 + strlen(TestString0));
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }
    else if( strcmp(argv[1], "Mix") == 0 ) {
        int p = 4711;
        for(int i = 0; i != 10; ++i) {
            p = (p + i) * (p + i) % 4711;  // pseudo random number
            if( p % 2 == 0 )
                QUEX_NAME(Accumulator_add)(&accumulator, TestString0, TestString0 + strlen(TestString0));
            else {
                QUEX_NAME(Accumulator_add_character)(&accumulator, ' ');
                QUEX_NAME(Accumulator_add_character)(&accumulator, p % 26 + 'a');
                QUEX_NAME(Accumulator_add_character)(&accumulator, ' ');
            }
        }
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }

    QUEX_NAME(Accumulator_destruct)(&accumulator);

    return 0;
}
