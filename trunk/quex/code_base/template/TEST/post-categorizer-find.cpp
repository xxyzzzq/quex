#include <cstdio>
#include <cstdlib>
#include <cstring>
#define QUEX_TYPE_CHARACTER char
#define QUEX_TYPE_TOKEN_ID  int
#define QUEX_OPTION_POST_CATEGORIZER
#include <quex/code_base/template/PostCategorizer.i>

void test(quex::QuexPostCategorizer* pc, const char* Name);

int
main(int argc, char** argv)
{
    using namespace quex;

    if( argc < 2 ) return -1;

    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Post Categorizer: Enter;\n");
        printf("CHOICES: 0, 1, 2, 3, 4, 5, 6;\n");
        return 0;
    }
    const int Start = atoi(argv[1]);
    QuexPostCategorizer  pc;

    QuexPostCategorizer_construct(&pc);
    /* The 'Start' value tells where the insertion starts. => Tree configuration */
    for(int i=0; i<7; ++i) {
        if     ( (i + Start) % 7 == 0 ) QuexPostCategorizer_insert(&pc, "Albert",  1);
        else if( (i + Start) % 7 == 1 ) QuexPostCategorizer_insert(&pc, "Alfons",  2);
        else if( (i + Start) % 7 == 2 ) QuexPostCategorizer_insert(&pc, "Alfred",  3);
        else if( (i + Start) % 7 == 3 ) QuexPostCategorizer_insert(&pc, "Alfrigo", 4);
        else if( (i + Start) % 7 == 4 ) QuexPostCategorizer_insert(&pc, "Ben",     5);
        else if( (i + Start) % 7 == 5 ) QuexPostCategorizer_insert(&pc, "Bert",    6);
        else if( (i + Start) % 7 == 6 ) QuexPostCategorizer_insert(&pc, "Bill",    7);
    }
    // QuexPostCategorizer_print_tree(pc.root, 0);
    test(&pc, "Abend");   /* NOT */
    test(&pc, "Albert");
    test(&pc, "Alcordo"); /* NOT */
    test(&pc, "Alfons");
    test(&pc, "Alfpump"); /* NOT */
    test(&pc, "Alfred");
    test(&pc, "Alfred");  /* NOT */
    test(&pc, "Alfrigo");
    test(&pc, "Alfrime");/* NOT */
    test(&pc, "Bam");    /* NOT */
    test(&pc, "Ben");
    test(&pc, "Beppo");  /* NOT */
    test(&pc, "Bert");
    test(&pc, "Berg");   /* NOT */
    test(&pc, "Bill");
    test(&pc, "Bully");  /* NOT */
}

void test(quex::QuexPostCategorizer* pc, const char* Name)
{
    using namespace quex;
    QuexPostCategorizerNode* found = QuexPostCategorizer_find(pc, Name);
    printf("%s:", Name);
    for(size_t i=0; i<10 - std::strlen(Name); ++i) printf(" ");
    if( found != 0x0 ) {
        printf("[%c]%s, %i\n", found->name_first_character, found->name_remainder, found->token_id); 
    } else {
        printf("<none>\n"); 
    }
}
