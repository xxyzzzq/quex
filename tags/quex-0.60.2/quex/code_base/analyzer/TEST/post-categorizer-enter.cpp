#include <quex/code_base/analyzer/TEST/post-categorizer-common.h>

/* See: post-categorizer-common.c */
using namespace quex;
void post_categorizer_setup(QUEX_NAME(Dictionary)* me, int Seed);

int
main(int argc, char** argv)
{

    if( argc < 2 ) return -1;

    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Post Categorizer: Enter;\n");
        printf("CHOICES: 0, 1, 2, 3, 4, 5, 6;\n");
        return 0;
    }
    const int Start = atoi(argv[1]);
    QUEX_NAME(Dictionary)  pc;

    post_categorizer_setup(&pc, Start);

    QUEX_NAME(PostCategorizer_print_this)(&pc);
}
