#include <stdio.h> 

// (*) include lexical analyser header
#include "UTF16Lex"
#include "UTF16Lex-token.i"

int 
main(int argc, char** argv) 
{        
    Token*       token;
    bool         BigEndianF = (argc < 2 || (strcmp(argv[1], "BE") == 0)); 
    const char*  file_name  = BigEndianF ? "example-utf16be.txt" : "example-utf16le.txt";

    if( argc == 1 ) return 0;

   
    /* NOTE: On a big endian machine (e.g. PowerPC) the byte reversion flag
     *       might be set to 'not BigEndianF'                                */
    UTF16Lex     qlex;

    QUEX_NAME(construct_file_name)(&qlex, file_name, 0x0, BigEndianF);

    printf("## input file           = %s\n", file_name);
    printf("## byte order reversion = %s\n", qlex.byte_order_reversion() ? "true" : "false");
    
    do {
        token = QUEX_NAME(receive)(&qlex);

        printf("%s\t", (char*)token->type_id_name().c_str());
        for(QUEX_TYPE_CHARACTER* iterator = (QUEX_TYPE_CHARACTER*)(token->get_text()).c_str();
            *iterator; ++iterator) {
            printf("%04X.", *iterator);
        }
        printf("\n");

        // (*) check against 'termination'
    } while( token->_id != TKN_TERMINATION );

    return 0;
}
