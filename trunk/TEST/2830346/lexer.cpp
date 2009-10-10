#include<cstdio> 

#include "max"
#include "moritz"
#include "boeck"

using namespace std;

template <class T>
void test(const char* Name, T& lexer, QUEX_TYPE_TOKEN_WITH_NAMESPACE_ID TokenID_Termination)
{
    printf("---------------------------------\n");
    printf(" %s:\n", Name);
    quex::Token   token;
    do {
        lexer.receive(&token);
        if( token.type_id() == TKN_OK ) continue;
        printf("%s\t", (char*)token.type_id_name().c_str());
        printf("%s\n", (char*)(token.text()).c_str());
    } while( token.type_id() != TokenID_Termination );
}

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::max     max_lex("example.txt");
    quex::moritz  moritz_lex("example.txt");
    quex::boeck   boeck_lex("example.txt");

    test("Max",    max_lex,    MAX_TKN_TERMINATION);
    test("Moritz", moritz_lex, MORITZ_TKN_TERMINATION);
    test("Boeck",  boeck_lex,  TKN_TERMINATION);

    return 0;
}

