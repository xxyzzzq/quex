#include<stdio.h> 

#include "moritz_Lexer.h"
#include "max_Lexer.h"
#include "boeck_Lexer.h"

/* When using multiple lexical analyzers, it must be compiled with 
 * QUEX_OPTION_MULTI and 'multi.i' must be included in one single file.      */
#include <quex/code_base/multi.i>


int 
main(int argc, char** argv) 
{        
    /* We want to have error outputs in stdout, so that the unit test could 
     * see it.                                                               */
    max_Lexer     max_lex;
    moritz_Lexer  moritz_lex;
    boeck_Lexer   boeck_lex;
    A_B_C_Token*  max_token    = 0x0;
    A_B_C_Token*  moritz_token = 0x0;
    A_B_C_Token*  boeck_token  = 0x0;
    const size_t  BufferSize = 1024;
    char          buffer[1024];
    size_t        i = 0;

    max_Lexer_from_file_name(&max_lex,       "ucs4.txt", "UCS4");
    moritz_Lexer_from_file_name(&moritz_lex, "ucs4.txt", "UCS4");
    boeck_Lexer_from_file_name(&boeck_lex,   "ucs4.txt", "UCS4");

    /* Each lexer reads one token, since the grammars are similar the lexeme 
     * is always the same.                                                   */
    printf("                Max:        Moritz:      Boeck:\n");

    max_token    = max_Lexer_token_p(&max_lex);
    moritz_token = moritz_Lexer_token_p(&moritz_lex);
    boeck_token  = boeck_Lexer_token_p(&boeck_lex);

    do {
        (void)max_Lexer_receive(&max_lex);
        (void)moritz_Lexer_receive(&moritz_lex);
        (void)boeck_Lexer_receive(&boeck_lex);

        /* Lexeme is same for all three.                                     */
        printf("%s", A_B_C_Token_pretty_char_text(boeck_token, buffer, 
                                                  BufferSize));

        size_t      preL   = (size_t)strlen((const char*)boeck_token->text);
        size_t      L      = preL < 10 ? preL : 10;
        for(i=0; i < 10 - L ; ++i) printf(" ");
        printf("\t");
        printf("%s   %s   %s\n", 
               A_B_C_Token_map_id_to_name(max_token->_id),
               A_B_C_Token_map_id_to_name(moritz_token->_id),
               A_B_C_Token_map_id_to_name(boeck_token->_id));

    } while( boeck_token->_id != TKN_TERMINATION );

    boeck_Lexer_destruct(&boeck_lex);
    max_Lexer_destruct(&max_lex);
    moritz_Lexer_destruct(&moritz_lex);

    return 0;
}

