#include<string.h>
#include<stdio.h>

#include "EHLexer.h"

#define FLUSH() do { fflush(stdout); fflush(stderr); } while(0)

int 
main(int argc, char** argv) 
{        
    const size_t        BufferSize = 1024;
    char                buffer[1024];
    QUEX_TYPE_TOKEN*    token_p = 0x0;
    QUEX_TYPE_TOKEN_ID  token_id = 0;
    char                file_name[256];
    quex_EHLexer        qlex;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf(__TEST_DESCRIPTION ";\n");
        printf("CHOICES: " __TEST_CHOICES ";\n");
        return 0;
    }

    snprintf(file_name, (size_t)256, "./examples/%s.txt", (const char*)argv[1]);
    /* printf("%s\n", file_name); */
    QUEX_NAME(construct_file_name)(&qlex, file_name, (const char*)0x0, false);
    FLUSH();

    fprintf(stderr, "| [START]\n");
    FLUSH();

    token_p = QUEX_NAME(token_p)(&qlex);
    do {
        token_id = QUEX_NAME(receive)(&qlex);
        FLUSH();
        printf("TOKEN: %s\n", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));
        FLUSH();
    } while( token_id != TK_TERMINATION );

    fprintf(stderr, "| [END]\n");
    FLUSH();

    return 0;
}
