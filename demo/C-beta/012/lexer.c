#include <stdio.h> 

#include "moritz_Lexer"
#include "max_Lexer"
#include "boeck_Lexer"

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    max_Lexer     max_lex;
    moritz_Lexer  moritz_lex;
    boeck_Lexer   boeck_lex;
    max_Token*    max_token    = 0x0;
    moritz_Token* moritz_token = 0x0;
    boeck_Token*  boeck_token  = 0x0;

    max_Lexer_construct_file_name(&max_lex, "example-utf16.txt", "UTF16", false);
    moritz_Lexer_construct_file_name(&moritz_lex, "example-ucs2.txt", "UCS-2", false);
    boeck_Lexer_construct_file_name(&boeck_lex, "example-utf8.txt", 0x0, false);

    // Each lexer reads one token, since the grammars are similar the lexeme 
    // is always the same.                                                    
    printf("                Max:        Moritz:      Boeck:\n");

    max_token    = max_Lexer_token_p(&max_lex);
    moritz_token = moritz_Lexer_token_p(&moritz_lex);
    boeck_token  = boeck_Lexer_token_p(&boeck_lex);
    do {
        (void)max_lex.receive();
        (void)moritz_lex.receive();
        (void)boeck_lex.receive();

        /* Lexeme is same for all three. */
        char* lexeme = (char*)max_token->utf8_text().c_str();
        int   L      = (int)std::strlen(lexeme);

        printf(lexeme);

        for(int i=0; i < 10 - L ; ++i) printf(" ");
        printf("\t");
        printf("%s   %s   %s\n", 
               max_token->type_id_name().c_str(), 
               moritz_token->type_id_name().c_str(), 
               boeck_token->type_id_name().c_str());

    } while( boeck_token->_id != TKN_TERMINATION );

    return 0;
}

