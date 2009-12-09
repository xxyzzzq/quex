#include<cstdio> 

#include "moritz_Lexer"
#include "max_Lexer"
#include "boeck_Lexer"

using namespace std;

template <class LexerT, class TokenT>
void test(const char* Name, LexerT& lexer, QUEX_TYPE_TOKEN_ID TokenID_Termination, TokenT& token)
{
    printf("---------------------------------\n");
    printf(" %s:\n", Name);
    do {
        lexer.receive(&token);
        if( token.type_id() == TKN_OK ) continue;
        printf("%s\t", (char*)token.type_id_name().c_str());
        printf("%s\n", (char*)(token.get_text()).c_str());
    } while( token.type_id() != TokenID_Termination );
}

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    max::Lexer     max_lex("example.txt");
    max::Token     max_token;
    moritz::Lexer  moritz_lex("example.txt");
    moritz::Token  moritz_token;
    boeck::Lexer   boeck_lex("example.txt");
    boeck::Token   boeck_token;


    test("Max",    max_lex,    MAX_TKN_TERMINATION,    max_token);
    test("Moritz", moritz_lex, MORITZ_TKN_TERMINATION, moritz_token);
    test("Boeck",  boeck_lex,  TKN_TERMINATION,        boeck_token);

    return 0;
}

