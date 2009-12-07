#include <cstdio>
#include <cstdlib>
#include <cstring>
#define QUEX_TYPE_CHARACTER char
#define QUEX_TYPE_TOKEN_ID  int
#define QUEX_OPTION_STRING_ACCUMULATOR
#define QUEX_TYPE_ANALYZER       TestAnalyzer
#include <quex/code_base/analyzer/configuration/default>

QUEX_NAMESPACE_MAIN_OPEN

typedef struct { } Token;

struct TestAnalyzer {
    void  send(QUEX_TYPE_TOKEN_ID TokenID, QUEX_TYPE_CHARACTER* Msg) {
        printf("Lexical Analyzer Receives:\n");
        printf("   '%s'\n", Msg);
    }
    struct {
        struct {
            size_t  _column_number_at_begin;
            size_t  _line_number_at_begin;
        } base;
    } counter;
};

QUEX_NAMESPACE_MAIN_CLOSE

// Prevent the inclusion of 'token-sending.i' since we do it on our own.
#define  __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__TOKEN_SENDING_I
#include <quex/code_base/analyzer/Accumulator>
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

    QUEX_NAME(Accumulator_construct)(&accumulator, &analyzer);

    if     ( strcmp(argv[1], "String") == 0 ) {
        accumulator.add(TestString0, TestString0 + strlen(TestString0));
        accumulator.print_this();
        accumulator.flush(0);
    }
    else if( strcmp(argv[1], "Character") == 0 ) {
        accumulator.add_chararacter('a');
        accumulator.print_this();
        accumulator.flush(0);
    }
    else if( strcmp(argv[1], "N-Character") == 0 ) {
        for(int i = 0; i != 104; ++i) 
            accumulator.add_chararacter(i % 26 + 'a');
        accumulator.print_this();
        accumulator.flush(0);
    }
    else if( strcmp(argv[1], "N-String") == 0 ) {
        for(int i = 0; i != 10; ++i) 
            accumulator.add(TestString0, TestString0 + strlen(TestString0));
        accumulator.print_this();
        accumulator.flush(0);
    }
    else if( strcmp(argv[1], "Mix") == 0 ) {
        int p = 4711;
        for(int i = 0; i != 10; ++i) {
            p = (p + i) * (p + i) % 4711;  // pseudo random number
            if( p % 2 == 0 )
                accumulator.add(TestString0, TestString0 + strlen(TestString0));
            else {
                accumulator.add_chararacter(' ');
                accumulator.add_chararacter(p % 26 + 'a');
                accumulator.add_chararacter(' ');
            }
        }
        accumulator.print_this();
        accumulator.flush(0);
    }

    QUEX_NAME(Accumulator_destruct)(&accumulator);

    return 0;
}
