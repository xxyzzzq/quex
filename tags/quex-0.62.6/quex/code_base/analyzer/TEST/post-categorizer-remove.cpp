#include <quex/code_base/analyzer/TEST/post-categorizer-common.h>

using namespace quex;
void post_categorizer_setup(QUEX_NAME(Dictionary)* me, int Seed);
void test(quex::QUEX_NAME(Dictionary)* pc, const char* Name);

int
main(int argc, char** argv)
{
    using namespace quex;

    if( argc < 2 ) return -1;

    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Post Categorizer: Remove Non-Existent Node;\n");
        printf("CHOICES: Aa, Ac, Ae, Ag, Ai, Ba, Bc, Be;\n");
        printf("SAME;\n");
        return 0;
    }
    QUEX_NAME(Dictionary)  pc;

    post_categorizer_setup(&pc, 4);
    
    pc.remove(argv[1]);

    QUEX_NAME(PostCategorizer_print_this)(&pc);
}
