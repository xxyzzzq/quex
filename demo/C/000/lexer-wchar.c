#include <stdio.h>
#include <assert.h>

#include "LexUtf8WChar.h"

void
get_wfile_input(quex_LexUtf8WChar* qlex);

int 
main(int argc, char** argv) 
{        
    quex_LexUtf8WChar qlex;
    int               number_of_tokens = 0;
    const size_t      BufferSize = 1024;
    char              buffer[1024];

    get_wfile_input(&qlex);

    printf(",-----------------------------------------------------------------\n");
    printf("| [START]\n");

    do {
        QUEX_NAME(receive)(&qlex);
        /* print out token information */
        printf("%s \n", QUEX_NAME_TOKEN(get_string)(qlex.token, buffer, BufferSize));
 
        ++number_of_tokens;
    } while( qlex.token->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", number_of_tokens);
    printf("`-----------------------------------------------------------------\n");

    QUEX_NAME(destruct)(&qlex);

    return 0;
}

void
get_wfile_input(quex_LexUtf8WChar* qlex)
{
    /* We write the file ourselves so that there is never an issue about alignment */
    wchar_t    original[] = L"bonjour le monde hello world hallo welt";
    uint8_t*   End        = (uint8_t*)(original + sizeof(original)/sizeof(wchar_t));
    uint8_t*   p          = 0x0;
    FILE*      fh         = 0x0;

    fh = fopen("wchar_t-example.txt", "w");

    /* Write the wchar_t byte by byte as we have it in memory */
    for(p = (uint8_t*)original; p != End; ++p) fputc(*p, fh);
    fclose(fh);

    /* Normal File Input */
    printf("## FILE* (stdio.h):\n");
    printf("##    Note this works only when engine is generated with -b wchart_t\n");
    printf("##    and therefore QUEX_TYPE_LEXATOM == uint16_t.\n");

    assert(sizeof(QUEX_TYPE_LEXATOM) == sizeof(wchar_t));

    QUEX_NAME(from_file_name)(qlex, "wchar_t-example.txt", 0x0);
}

