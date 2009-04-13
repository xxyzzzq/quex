#include <cstdio>
#include <cstdlib>
#include <cstring>
#define QUEX_TYPE_CHARACTER char
#define QUEX_TYPE_TOKEN_ID  int
#define QUEX_OPTION_POST_CATEGORIZER
#include <quex/code_base/template/PostCategorizer.i>

int
main(int argc, char** argv)
{
    using namespace quex;

    if( argc < 2 ) return -1;

    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Post Categorizer: Enter;\n");
        printf("CHOICES: 1, 2, 3, 4;\n");
        printf("SAME;\n");
        return 0;
    }
    const int Start = atoi(argv[1]);
    QuexPostCategorizer  pc;

    QuexPostCategorizer_construct(&pc);
    /* The 'Start' value tells where the insertion starts. */
    for(int i=0; i<4; ++i) {
        if     ( (i + Start) % 4 == 0 ) QuexPostCategorizer_insert(&pc, "Albert", 1);
        else if( (i + Start) % 4 == 1 ) QuexPostCategorizer_insert(&pc, "Alfons", 2);
        else if( (i + Start) % 4 == 2 ) QuexPostCategorizer_insert(&pc, "Alfred", 3);
        else if( (i + Start) % 4 == 3 ) QuexPostCategorizer_insert(&pc, "Alfrigo", 4);
    }
    QuexPostCategorizer_print_tree(pc.root, 0);
}
