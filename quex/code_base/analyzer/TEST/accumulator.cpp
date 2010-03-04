#include <cstdio>
#include <cstdlib>
#include <cstring>
#define QUEX_TYPE_CHARACTER  char
#define QUEX_TYPE_TOKEN_ID   int
#define QUEX_TYPE_ANALYZER   TestAnalyzer
#define QUEX_OPTION_STRING_ACCUMULATOR

#include <quex/code_base/analyzer/configuration/default>

QUEX_NAMESPACE_MAIN_OPEN
class TestAnalyzer;
QUEX_NAMESPACE_MAIN_OPEN

#include <quex/code_base/analyzer/Accumulator>

QUEX_NAMESPACE_MAIN_OPEN

//#define QUEX_TOKEN_POLICY_SET_ID()       /* empty */
//#define QUEX_TOKEN_POLICY_PREPARE_NEXT() /* empty */

typedef struct { int _id; } Token;


class TestAnalyzer {
public:
    struct { 
        QUEX_TYPE_TOKEN   begin[1];
        QUEX_TYPE_TOKEN*  write_iterator;
        QUEX_TYPE_TOKEN*  read_iterator;
        QUEX_TYPE_TOKEN*  memory_end;
    } _token_queue;
    struct {
        struct {
            size_t  _column_number_at_begin;
            size_t  _line_number_at_begin;
        } base;
    } counter;

    QUEX_NAME(Accumulator) accumulator;
};

bool 
QUEX_NAME_TOKEN(take_text)(QUEX_TYPE_TOKEN*                           __this, 
                           QUEX_NAMESPACE_MAIN::QUEX_TYPE_ANALYZER*   analyzer, 
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
    TestAnalyzer           analyzer;
    QUEX_NAME(Accumulator) accumulator;

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
        QUEX_NAME(Accumulator_add_chararacter)(&accumulator, 'a');
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }
    else if( strcmp(argv[1], "N-Character") == 0 ) {
        for(int i = 0; i != 104; ++i) 
            QUEX_NAME(Accumulator_add_chararacter)(&accumulator, i % 26 + 'a');
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
                QUEX_NAME(Accumulator_add_chararacter)(&accumulator, ' ');
                QUEX_NAME(Accumulator_add_chararacter)(&accumulator, p % 26 + 'a');
                QUEX_NAME(Accumulator_add_chararacter)(&accumulator, ' ');
            }
        }
        QUEX_NAME(Accumulator_print_this)(&accumulator);
        self_accumulator_flush(0);
    }

    QUEX_NAME(Accumulator_destruct)(&accumulator);

    return 0;
}
