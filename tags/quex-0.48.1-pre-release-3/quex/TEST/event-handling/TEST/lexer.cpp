#include<fstream>    
#include<iostream> 
#include<cstring>
#include<cstdio>

#include "EHLexer"

using namespace std;

int 
main(int argc, char** argv) 
{        

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf(__TEST_DESCRIPTION ";\n");
        printf("CHOICES: " __TEST_CHOICES ";\n");
        return 0;
    }
    quex::Token    Token;
    std::string    Directory("examples/");
    quex::EHLexer  qlex(Directory + argv[1] + ".txt");

    stderr = stdout;

    cout << "| [START]\n";

    do {
        qlex.receive(&Token);
        cout << "TOKEN: " << std::string(Token) << endl;
    } while( Token.type_id() != TK_TERMINATION );

    cout << "| [END]\n";

    return 0;
}
