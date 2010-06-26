#include <stdio.h>
#include<assert.h>

#include "tiny_wlexer"
#include "tiny_wlexer-token.i"

using namespace std;

quex::tiny_wlexer*  get_wstringstream_input();
quex::tiny_wlexer*  get_wfile_input();


int 
main(int argc, char** argv) 
{        
    QUEX_TYPE_TOKEN*  token = 0x0;
    tiny_wlexer       qlex;
    int               number_of_tokens = 0;
    const size_t      UTF8ContentSize = 1024;
    uint8_t           utf8_content[1024];
    uint8_t*          end = (uint8_t)0x0;

    get_wfile_input(&qlex);

    printf(",-----------------------------------------------------------------\n");
    printf("| [START]\n");

    do {
        token = qlex->receive();
        /* print out token information */
 
        ++number_of_tokens;
    } while( token->type_id() != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", number_of_tokens);
    printf("`-----------------------------------------------------------------\n");

    QUEX_NAME(destruct)(&qlex);

    return 0;
}

quex::tiny_wlexer* 
get_wfile_input(tiny_lexer* qlex)
{
    /* We write the file ourselves so that there is never an issue about alignment */
    wchar_t    original[] = L"bonjour le monde hello world hallo welt";
    uint8_t*   End        = (uint8_t*)(original + wcslen(original));
    FILE*      fh = 0x0;

    fh = fopen("wchar_t-example.txt", "w");

    /* Write the wchar_t byte by byte as we have it in memory */
    for(uint8_t* p = (uint8_t*)original; p != End; ++p) fputc(*p, fh);
    fclose(fh);

    /* Normal File Input */
    printf("## FILE* (stdio.h):\n");
    printf("##    Note this works only when engine is generated with -b wchart_t\n");
    printf("##    and therefore QUEX_TYPE_CHARACTER == uint16_t.\n");

    assert(sizeof(QUEX_TYPE_CHARACTER) == sizeof(wchar_t));

    QUEX_NAME(construct_file_name)(qlex, "example.txt", 0x0, false);
}

quex::tiny_wlexer* 
get_wstringstream_input()
{
    /* Wide String Stream Input */
    std::wstringstream    my_stream;
    cout << "## wstringstream:\n";
    cout << "##    Note this works only when engine is generated with -b wchar_t\n";
    cout << "##    and therefore QUEX_TYPE_CHARACTER == wchar_t.\n";

    assert(sizeof(QUEX_TYPE_CHARACTER) == sizeof(wchar_t));

    my_stream << L"bonjour le monde hello world hallo welt";

    return new quex::tiny_wlexer(&my_stream);
}
