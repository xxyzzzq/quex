#include <stdio.h> 

// (*) include lexical analyser header
#include "UTF16Lex.h"

int 
main(int argc, char** argv) 
{        
    quex_Token*              token_p     = 0x0;
    bool                     BigEndianF  = (argc < 2 || (strcmp(argv[1], "BE") == 0)); 
    const char*              file_name   = BigEndianF ? "example-utf16be.txt" : "example-utf16le.txt";
    ByteLoader*              byte_loader = ByteLoader_FILE_new_from_file_name(file_name);
    QUEX_NAME(BufferFiller)* filler      = QUEX_NAME(BufferFiller_new)(byte_loader, 0, 0);
    quex_UTF16Lex            qlex;
    size_t                   BufferSize = 1024;
    char                     buffer[1024];

    if( argc == 1 ) {
        printf("Required at least one argument: 'LE' or 'BE'.\n");
        return -1;
    }
   
    /* System's endianness is 'little' => reversion if 'big'
     *                     is 'big'    => reversion if 'little' (not 'big'). */
    filler->_byte_order_reversion_active_f = QUEXED(system_is_little_endian)() ? 
                                             BigEndianF : ! BigEndianF;
    QUEX_NAME(from_BufferFiller)(&qlex, filler);

    printf("## input file           = %s\n", file_name);
    printf("## byte order reversion = %s\n", QUEX_NAME(byte_order_reversion)(&qlex) ? "true" : "false");
    
    do {
        QUEX_NAME(receive)(&qlex, &token_p);

        /* Print the lexeme in utf8 format. */
        printf("%s \n", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));

        // (*) check against 'termination'
    } while( token_p->_id != TKN_TERMINATION );

    QUEX_NAME(destruct)(&qlex);
    filler->delete_self(filler);
    byte_loader->delete_self(byte_loader);
    return 0;
}
