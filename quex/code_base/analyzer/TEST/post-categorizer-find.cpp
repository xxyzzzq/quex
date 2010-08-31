#include <cstdio>
#include <cstdlib>
#include <cstring>
#define QUEX_TYPE_CHARACTER char
#define QUEX_TYPE_TOKEN_ID  int
#define QUEX_OPTION_POST_CATEGORIZER
#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/analyzer/PostCategorizer.i>
#include <quex/code_base/aux-string.i>

using namespace quex;
void post_categorizer_setup(QUEX_NAME(Dictionary)* me, int Seed);
void test(quex::QUEX_NAME(Dictionary)* pc, const char* Name);

int
main(int argc, char** argv)
{
    using namespace quex;

    if( argc < 2 ) return -1;

    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Post Categorizer: Enter;\n");
        printf("CHOICES: 0, 1, 2, 3, 4, 5, 6;\n");
        printf("SAME;\n");
        return 0;
    }
    const int Start = atoi(argv[1]);
    QUEX_NAME(Dictionary)  pc;

    post_categorizer_setup(&pc, Start);
    
    // QUEX_NAME(Dictionary_print_tree(pc.root, 0);
    test(&pc, "Aa");
    test(&pc, "Ab");
    test(&pc, "Ac");
    test(&pc, "Ad");
    test(&pc, "Ae");
    test(&pc, "Af");
    test(&pc, "Ag");
    test(&pc, "Ah");
    test(&pc, "Ai");
    test(&pc, "Ba"); 
    test(&pc, "Bb"); 
    test(&pc, "Bc"); 
    test(&pc, "Bd"); 
    test(&pc, "Be"); 
    test(&pc, "Bf"); 
    test(&pc, "Bg"); 
}

void test(QUEX_NAME(Dictionary)* pc, const char* Name)
{
    using namespace quex;
    QUEX_NAME(DictionaryNode)* found = QUEX_NAME(PostCategorizer_find)(pc, Name);
    printf("%s: ", Name);
    if( found != 0x0 ) {
        printf("[%c]%s, %i\n", found->name_first_character, found->name_remainder, found->token_id); 
    } else {
        printf("<none>\n"); 
    }
}
