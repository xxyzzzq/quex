#include<cstdio> 
#include<cstdlib> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;

int 
main(int argc, char** argv) 
{        
    quex::Token*   token_p = 0x0;
#   if   defined (__QUEX_SETTING_TEST_UTF8)
    FILE*          fh = fopen("example-hindi.utf8", "r");
#   else
    FILE*          fh = fopen("example.txt", "r");
#   endif
#   ifdef __QUEX_OPTION_CONVERTER
    quex::Simple   qlex(fh, "UTF8");
#   else
    quex::Simple   qlex(fh);
#   endif

    if( argc < 2 ) {
        printf("Command line argument required!\n");
        return 0;
    }
    if( strcmp(argv[1], "--hwut-info") == 0 ) {
#       if   defined(QUEX_OPTION_ENABLED_ICONV)
        printf("Reset w/ QuexBufferFiller: Converter_IConv;\n");
#       elif defined(QUEX_OPTION_ENABLED_ICU)
        printf("Reset w/ QuexBufferFiller: Converter_ICU;\n");
#       elif defined(__QUEX_SETTING_TEST_UTF8)
        printf("Reset w/ QuexBufferFiller: Plain w/ Engine Codec;\n");
#       else
        printf("Reset w/ QuexBufferFiller: Plain;\n");
#       endif
        printf("CHOICES:  0, 1, 2, 3, 20, 30, 50, 134, 135, 136, 1000;\n");
        printf("SAME;\n");
        return 0;
    }
    int N = atoi(argv[1]);

    /* Read 'N' tokens before doing the reset. */
    token_p = qlex.token_p();
    for(int i=0; i < N; ++i) {
        (void)qlex.receive();
    } 

    qlex.reset();

    printf("## repeated: %i\n", N);

    do {
        (void)qlex.receive();

#       if defined (__QUEX_OPTION_CONVERTER)
        printf("(%2i, %2i)   \t%s '%s' \n", (int)qlex.line_number(), (int)qlex.column_number(),
               token_p->type_id_name().c_str(), token_p->pretty_char_text().c_str());
#       else
        printf("(%2i, %2i)   \t%s '%s' \n", (int)qlex.line_number(), (int)qlex.column_number(),
               token_p->type_id_name().c_str(), (const char*)token_p->text.c_str());
#       endif

    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    return 0;
}
