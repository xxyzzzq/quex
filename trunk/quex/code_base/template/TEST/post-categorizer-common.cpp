#define QUEX_TYPE_CHARACTER char
#define QUEX_TYPE_TOKEN_ID  int
#define QUEX_OPTION_POST_CATEGORIZER
#include <quex/code_base/template/PostCategorizer.i>

void post_categorizer_setup(QuexPostCategorizer* me, int Seed)
{
    QuexPostCategorizer_construct(&pc);
    /* The 'Seed' value tells where the insertion starts. */
    for(int i=0; i<7; ++i) {
        if     ( (i + Seed) % 7 == 0 ) QuexPostCategorizer_insert(&pc, "Aa", 1);
        else if( (i + Seed) % 7 == 1 ) QuexPostCategorizer_insert(&pc, "Ac", 2);
        else if( (i + Seed) % 7 == 2 ) QuexPostCategorizer_insert(&pc, "Ae", 3);
        else if( (i + Seed) % 7 == 3 ) QuexPostCategorizer_insert(&pc, "Ag", 4);
        else if( (i + Seed) % 7 == 4 ) QuexPostCategorizer_insert(&pc, "Ba", 5);
        else if( (i + Seed) % 7 == 5 ) QuexPostCategorizer_insert(&pc, "Bc", 6);
        else if( (i + Seed) % 7 == 6 ) QuexPostCategorizer_insert(&pc, "Be", 7);
    }
}
