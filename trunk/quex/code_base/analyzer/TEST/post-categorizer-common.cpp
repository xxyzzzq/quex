#define QUEX_TYPE_CHARACTER char
#define QUEX_TYPE_TOKEN_ID  int
#define QUEX_OPTION_POST_CATEGORIZER
#include <quex/code_base/test_environment/default_configuration>
#include <quex/code_base/analyzer/PostCategorizer.i>

using namespace quex;

void post_categorizer_setup(QuexPostCategorizer* me, int Seed)
{
    QuexPostCategorizer_construct(me);
    /* The 'Seed' value tells where the enterion starts. */
    for(int i=0; i<7; ++i) {
        if     ( (i + Seed) % 7 == 0 ) QuexPostCategorizer_enter(me, "Ab", 1);
        else if( (i + Seed) % 7 == 1 ) QuexPostCategorizer_enter(me, "Ad", 2);
        else if( (i + Seed) % 7 == 2 ) QuexPostCategorizer_enter(me, "Af", 3);
        else if( (i + Seed) % 7 == 3 ) QuexPostCategorizer_enter(me, "Ah", 4);
        else if( (i + Seed) % 7 == 4 ) QuexPostCategorizer_enter(me, "Bb", 5);
        else if( (i + Seed) % 7 == 5 ) QuexPostCategorizer_enter(me, "Bd", 6);
        else if( (i + Seed) % 7 == 6 ) QuexPostCategorizer_enter(me, "Bf", 7);
    }
}
