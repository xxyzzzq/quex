#include<cstdio> 

#include "moritz_Lexer.h"
#include "max_Lexer.h"
#include "boeck_Lexer.h"

using namespace std;


int 
main(int argc, char** argv) 
{        
    /* we want to have error outputs in stdout, so that the unit test could see it. */
    quex_max_Lexer     max_lex;
    quex_moritz_Lexer  moritz_lex;
    quex_boeck_Lexer   boeck_lex;
    quex_Common_Token* max_token    = 0x0;
    quex_Common_Token* moritz_token = 0x0;
    quex_Common_Token* boeck_token  = 0x0;

    max_Lexer_construct_file_name(&max_lex,       "example.txt", 0x0, false);
    moritz_Lexer_construct_file_name(&moritz_lex, "example.txt", 0x0, false);
    boeck_Lexer_construct_file_name(&boeck_lex,   "example.txt", 0x0, false);

    // Each lexer reads one token, since the grammars are similar the lexeme 
    // is always the same.                                                    
    printf("                Max:        Moritz:      Boeck:\n");

    max_token    = max_lex.token_p();
    moritz_token = moritz_lex.token_p();
    boeck_token  = boeck_lex.token_p();
    do {
        (void)max_lex.receive();
        (void)moritz_lex.receive();
        (void)boeck_lex.receive();

        /* Lexeme is same for all three. */
        char* lexeme = (char*)max_token->pretty_char_text().c_str();
        int   L      = (int)max_token->text.length();

        printf("%s", lexeme);

        for(int i=0; i < 10 - L ; ++i) printf(" ");
        printf("\t");
        printf("%s   %s   %s\n", 
               max_token->type_id_name().c_str(), 
               moritz_token->type_id_name().c_str(), 
               boeck_token->type_id_name().c_str());

    } while( boeck_token->type_id() != TKN_TERMINATION );

    return 0;
}

