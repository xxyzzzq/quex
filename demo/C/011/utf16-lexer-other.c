#include <stdio.h> 

// (*) include lexical analyser header
#include "UTF16Lex.h"

int 
main(int argc, char** argv) 
{        
    quex_Token*                 token_p     = 0x0;
    bool                        BigEndianF  = (argc < 2 || (strcmp(argv[1], "BE") == 0)); 
    const char*                 file_name   = BigEndianF ? "example-other-utf16be.txt" : "example-other-utf16le.txt";
    QUEX_NAME(ByteLoader)*      byte_loader = QUEX_NAME(ByteLoader_FILE_new_from_file_name)(file_name);
    QUEX_NAME(BufferFiller)*    filler      = QUEX_NAME(BufferFiller_new)(byte_loader, 0, 0);
    quex_UTF16Lex               qlex;
    const QUEX_TYPE_CHARACTER*  iterator = 0x0;

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

        printf("%s\t", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        for(iterator = token_p->text; *iterator; ++iterator) {
            printf("%04X.", (int)*iterator);
        }
        printf("\n");

        // (*) check against 'termination'
    } while( token_p->_id != TKN_TERMINATION );

    QUEX_NAME(destruct)(&qlex);
    filler->delete_self(filler);
    byte_loader->delete_self(byte_loader);

    return 0;
}
